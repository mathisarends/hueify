import json
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from hueify.credentials import HueBridgeCredentials
from hueify.sse.bus import EventBus
from hueify.sse.stream import ServerSentEventStream


def make_credentials() -> HueBridgeCredentials:
    return HueBridgeCredentials(
        hue_bridge_ip="192.168.1.1",
        hue_app_key="a" * 20,
    )


def make_stream() -> tuple[ServerSentEventStream, AsyncMock]:
    credentials = make_credentials()
    bus = AsyncMock(spec=EventBus)
    stream = ServerSentEventStream(credentials=credentials, event_bus=bus)
    return stream, bus


def make_raw_event(resource_type: str = "light") -> dict:
    return {
        "id": str(uuid4()),
        "type": resource_type,
        "owner": {
            "rid": str(uuid4()),
            "rtype": "device",
        },
    }


def make_sse(data: object) -> MagicMock:
    sse = MagicMock()
    sse.data = json.dumps(data)
    return sse


class TestHandleSse:
    @pytest.mark.asyncio
    async def test_dispatches_event_from_valid_payload(self) -> None:
        stream, bus = make_stream()
        sse = make_sse([{"data": [make_raw_event()]}])

        await stream._handle_sse(sse)

        bus.dispatch.assert_called_once()

    @pytest.mark.asyncio
    async def test_dispatches_multiple_events_from_single_payload(self) -> None:
        stream, bus = make_stream()
        sse = make_sse([{"data": [make_raw_event(), make_raw_event()]}])

        await stream._handle_sse(sse)

        assert bus.dispatch.call_count == 2

    @pytest.mark.asyncio
    async def test_dispatches_events_from_multiple_containers(self) -> None:
        stream, bus = make_stream()
        sse = make_sse([{"data": [make_raw_event()]}, {"data": [make_raw_event()]}])

        await stream._handle_sse(sse)

        assert bus.dispatch.call_count == 2

    @pytest.mark.asyncio
    async def test_skips_container_without_data_key(self) -> None:
        stream, bus = make_stream()
        sse = make_sse([{"other": "field"}])

        await stream._handle_sse(sse)

        bus.dispatch.assert_not_called()

    @pytest.mark.asyncio
    async def test_does_not_raise_on_invalid_json(self) -> None:
        stream, bus = make_stream()
        sse = MagicMock()
        sse.data = "not valid json {"

        await stream._handle_sse(sse)

        bus.dispatch.assert_not_called()

    @pytest.mark.asyncio
    async def test_does_not_raise_when_dispatch_raises(self) -> None:
        stream, bus = make_stream()
        bus.dispatch.side_effect = RuntimeError("dispatch failed")
        sse = make_sse([{"data": [make_raw_event()]}])

        await stream._handle_sse(sse)


class TestDisconnect:
    def test_sets_is_running_to_false(self) -> None:
        stream, _ = make_stream()
        stream._is_running = True

        stream.disconnect()

        assert stream._is_running is False


class TestConnect:
    @pytest.mark.asyncio
    async def test_sets_is_running_to_false_after_connect(self) -> None:
        stream, _ = make_stream()

        async def fake_aiter_sse():
            stream.disconnect()
            return
            yield

        mock_event_source = MagicMock()
        mock_event_source.aiter_sse = fake_aiter_sse
        mock_event_source.__aenter__ = AsyncMock(return_value=mock_event_source)
        mock_event_source.__aexit__ = AsyncMock(return_value=False)

        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with (
            patch("hueify.sse.stream.httpx.AsyncClient", return_value=mock_client),
            patch("hueify.sse.stream.aconnect_sse", return_value=mock_event_source),
        ):
            await stream.connect()

        assert stream._is_running is False

    @pytest.mark.asyncio
    async def test_stops_processing_when_disconnected_mid_stream(self) -> None:
        stream, bus = make_stream()
        sse = make_sse([{"data": [make_raw_event()]}])

        async def fake_aiter_sse():
            stream.disconnect()
            yield sse

        mock_event_source = MagicMock()
        mock_event_source.aiter_sse = fake_aiter_sse
        mock_event_source.__aenter__ = AsyncMock(return_value=mock_event_source)
        mock_event_source.__aexit__ = AsyncMock(return_value=False)

        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with (
            patch("hueify.sse.stream.httpx.AsyncClient", return_value=mock_client),
            patch("hueify.sse.stream.aconnect_sse", return_value=mock_event_source),
        ):
            await stream.connect()

        bus.dispatch.assert_not_called()

    @pytest.mark.asyncio
    async def test_does_not_raise_on_connection_error(self) -> None:
        stream, _ = make_stream()

        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(side_effect=ConnectionError("refused"))
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("hueify.sse.stream.httpx.AsyncClient", return_value=mock_client):
            await stream.connect()
