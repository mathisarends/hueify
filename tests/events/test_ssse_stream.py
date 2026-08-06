import contextlib
import json
from collections.abc import Iterator, Sequence
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import httpx
import pytest

from hueify.credentials import HueBridgeCredentials
from hueify.errors import StreamAuthenticationError
from hueify.models import LightEvent
from hueify.sse.bus import EventBus
from hueify.sse.connection import StreamConnection
from hueify.sse.retry import ReconnectPolicy
from hueify.sse.stream import ServerSentEventStream

URL = "https://192.168.1.1/eventstream/clip/v2"


def make_credentials() -> HueBridgeCredentials:
    return HueBridgeCredentials(
        hue_bridge_ip="192.168.1.1",
        hue_app_key="a" * 20,
    )


def make_stream() -> tuple[ServerSentEventStream, AsyncMock, StreamConnection]:
    bus = AsyncMock(spec=EventBus)
    connection = StreamConnection()
    stream = ServerSentEventStream(
        credentials=make_credentials(),
        event_bus=bus,
        connection=connection,
        policy=ReconnectPolicy(),
    )
    return stream, bus, connection


def make_raw_event(resource_type: str = "light") -> dict:
    return {
        "id": str(uuid4()),
        "type": resource_type,
        "owner": {
            "rid": str(uuid4()),
            "rtype": "device",
        },
    }


def make_sse(data: object, event_id: str = "") -> MagicMock:
    sse = MagicMock()
    sse.data = json.dumps(data)
    sse.id = event_id
    return sse


def _async_cm(value: object) -> MagicMock:
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=value)
    cm.__aexit__ = AsyncMock(return_value=False)
    return cm


@contextlib.contextmanager
def patched_bridge(
    events: Sequence[MagicMock] = (),
    status_code: int = 200,
    connect_error: Exception | None = None,
) -> Iterator[dict[str, dict[str, str]]]:
    """Replace the bridge with a canned response and capture the request headers."""
    response = httpx.Response(status_code, request=httpx.Request("GET", URL))

    async def aiter_sse():
        for sse in events:
            yield sse

    event_source = MagicMock(response=response)
    event_source.aiter_sse = aiter_sse

    client = _async_cm(MagicMock())
    if connect_error is not None:
        client.__aenter__ = AsyncMock(side_effect=connect_error)

    sent: dict[str, dict[str, str]] = {}

    def fake_aconnect_sse(*, headers: dict[str, str], **_: object) -> MagicMock:
        sent["headers"] = headers
        return _async_cm(event_source)

    with (
        patch("hueify.sse.stream.httpx.AsyncClient", return_value=client),
        patch("hueify.sse.stream.aconnect_sse", side_effect=fake_aconnect_sse),
    ):
        yield sent


class TestHandleSse:
    @pytest.mark.asyncio
    async def test_dispatches_event_from_valid_payload(self) -> None:
        stream, bus, _ = make_stream()
        event = make_raw_event()
        event["unknown_future_field"] = {"nested": [1, 2, 3]}
        sse = make_sse([{"data": [event]}])

        await stream._handle_sse(sse)

        dispatched = bus.dispatch.await_args.args[0]
        assert isinstance(dispatched, LightEvent)
        assert dispatched.model_extra == {"unknown_future_field": {"nested": [1, 2, 3]}}

    @pytest.mark.asyncio
    async def test_dispatches_multiple_events_from_single_payload(self) -> None:
        stream, bus, _ = make_stream()
        sse = make_sse([{"data": [make_raw_event(), make_raw_event()]}])

        await stream._handle_sse(sse)

        assert bus.dispatch.call_count == 2

    @pytest.mark.asyncio
    async def test_dispatches_events_from_multiple_containers(self) -> None:
        stream, bus, _ = make_stream()
        sse = make_sse([{"data": [make_raw_event()]}, {"data": [make_raw_event()]}])

        await stream._handle_sse(sse)

        assert bus.dispatch.call_count == 2

    @pytest.mark.asyncio
    async def test_skips_container_without_data_key(self) -> None:
        stream, bus, _ = make_stream()
        sse = make_sse([{"other": "field"}])

        await stream._handle_sse(sse)

        bus.dispatch.assert_not_called()

    @pytest.mark.asyncio
    async def test_does_not_raise_on_invalid_json(self) -> None:
        stream, bus, _ = make_stream()
        sse = MagicMock()
        sse.data = "not valid json {"

        await stream._handle_sse(sse)

        bus.dispatch.assert_not_called()

    @pytest.mark.asyncio
    async def test_does_not_raise_when_dispatch_raises(self) -> None:
        stream, bus, _ = make_stream()
        bus.dispatch.side_effect = RuntimeError("dispatch failed")
        sse = make_sse([{"data": [make_raw_event()]}])

        await stream._handle_sse(sse)


class TestRunOnce:
    @pytest.mark.asyncio
    async def test_dispatches_received_events(self) -> None:
        stream, bus, _ = make_stream()

        with patched_bridge([make_sse([{"data": [make_raw_event()]}])]):
            await stream.run_once()

        bus.dispatch.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_marks_the_connection_open_while_consuming(self) -> None:
        stream, _, connection = make_stream()
        seen: list[bool] = []
        connection.on_change(lambda status: _record(seen, status.connected))

        with patched_bridge([make_sse([{"data": [make_raw_event()]}])]):
            await stream.run_once()

        assert seen == [True]
        assert connection.last_event_at is not None

    @pytest.mark.asyncio
    async def test_returns_when_the_bridge_ends_the_stream(self) -> None:
        stream, _, _ = make_stream()

        with patched_bridge():
            await stream.run_once()

    @pytest.mark.asyncio
    async def test_raises_on_connection_error(self) -> None:
        stream, _, _ = make_stream()

        with (
            patched_bridge(connect_error=httpx.ConnectError("refused")),
            pytest.raises(httpx.ConnectError),
        ):
            await stream.run_once()

    @pytest.mark.asyncio
    async def test_raises_authentication_error_on_rejected_key(self) -> None:
        stream, _, _ = make_stream()

        with patched_bridge(status_code=401), pytest.raises(StreamAuthenticationError):
            await stream.run_once()

    @pytest.mark.asyncio
    async def test_raises_status_error_on_server_failure(self) -> None:
        stream, _, _ = make_stream()

        with patched_bridge(status_code=503), pytest.raises(httpx.HTTPStatusError):
            await stream.run_once()

    @pytest.mark.asyncio
    async def test_first_connection_sends_no_resume_header(self) -> None:
        stream, _, _ = make_stream()

        with patched_bridge() as sent:
            await stream.run_once()

        assert "Last-Event-ID" not in sent["headers"]

    @pytest.mark.asyncio
    async def test_reconnect_resumes_after_the_last_seen_event(self) -> None:
        stream, _, _ = make_stream()
        sse = make_sse([{"data": [make_raw_event()]}], event_id="42")

        with patched_bridge([sse]):
            await stream.run_once()

        with patched_bridge() as sent:
            await stream.run_once()

        assert sent["headers"]["Last-Event-ID"] == "42"


async def _record(seen: list[bool], connected: bool) -> None:
    seen.append(connected)
