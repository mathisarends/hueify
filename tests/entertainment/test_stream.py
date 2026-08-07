import asyncio
import sys
from typing import Self
from unittest.mock import AsyncMock
from uuid import UUID

import pytest
from conftest import APP_KEY, CLIENT_KEY

from hueify.credentials import HueBridgeCredentials
from hueify.entertainment.namespace import EntertainmentNamespace
from hueify.entertainment.protocol import HEADER_LENGTH, frame_length
from hueify.entertainment.source import Tick
from hueify.entertainment.stream import MAX_RATE, EntertainmentStream
from hueify.errors import (
    EntertainmentError,
    MissingCredentialsError,
    MissingDependencyError,
)
from hueify.models import EntertainmentConfiguration

AREA_ID = UUID("a1b2c3d4-1111-2222-3333-444455556666")
BRIDGE_IP = "192.168.1.10"

SEQUENCE_BYTE = 11
CHANNELS_AT = HEADER_LENGTH + 36


def area_payload(channel_ids: tuple[int, ...] = (0, 1)) -> dict:
    return {
        "id": str(AREA_ID),
        "type": "entertainment_configuration",
        "metadata": {"name": "TV"},
        "configuration_type": "screen",
        "status": "inactive",
        "channels": [
            {
                "channel_id": channel_id,
                "position": {"x": -1 + channel_id, "y": 0.0, "z": 0.5},
                "members": [],
            }
            for channel_id in channel_ids
        ],
    }


def make_area(channel_ids: tuple[int, ...] = (0, 1)) -> EntertainmentConfiguration:
    return EntertainmentConfiguration.model_validate(area_payload(channel_ids))


class FakeConnection:
    """Records the datagrams the sender loop hands to the socket."""

    def __init__(self, fail_on_send: Exception | None = None) -> None:
        self.sent: list[bytes] = []
        self.closed = False
        self.connected_to: tuple[str, str, str] | None = None
        self._fail_on_send = fail_on_send

    def send(self, payload: bytes) -> None:
        if self._fail_on_send is not None:
            raise self._fail_on_send
        self.sent.append(payload)

    def close(self) -> None:
        self.closed = True


class FakeDtls:
    """A stand-in for the DTLS client, handing out one prepared connection."""

    def __init__(self, connection: FakeConnection) -> None:
        self.connection = connection

    async def connect(
        self, host: str, identity: str, client_key: str
    ) -> FakeConnection:
        self.connection.connected_to = (host, identity, client_key)
        return self.connection

    def install(self, monkeypatch: pytest.MonkeyPatch) -> Self:
        monkeypatch.setattr(
            "hueify.entertainment.stream._dtls_connection", lambda: self
        )
        return self


@pytest.fixture
def credentials() -> HueBridgeCredentials:
    return HueBridgeCredentials(
        hue_bridge_ip=BRIDGE_IP, hue_app_key=APP_KEY, hue_client_key=CLIENT_KEY
    )


@pytest.fixture
def areas() -> AsyncMock:
    namespace = AsyncMock(spec=EntertainmentNamespace)
    namespace.get_one.return_value = make_area()
    return namespace


@pytest.fixture
def connection() -> FakeConnection:
    return FakeConnection()


@pytest.fixture
def dtls(connection: FakeConnection, monkeypatch: pytest.MonkeyPatch) -> FakeDtls:
    return FakeDtls(connection).install(monkeypatch)


def make_stream(
    areas: AsyncMock,
    credentials: HueBridgeCredentials,
    area: object | None = None,
    rate: int = MAX_RATE,
) -> EntertainmentStream:
    return EntertainmentStream(
        area if area is not None else make_area(), areas, credentials, rate
    )


class TestOpening:
    def test_a_missing_client_key_says_where_to_get_one(
        self, areas: AsyncMock, without_stored_credentials: None
    ) -> None:
        without_client_key = HueBridgeCredentials(
            hue_bridge_ip=BRIDGE_IP, hue_app_key=APP_KEY
        )

        with pytest.raises(MissingCredentialsError, match="HUE_CLIENT_KEY"):
            EntertainmentStream(make_area(), areas, without_client_key)

    def test_an_impossible_rate_is_refused(
        self, areas: AsyncMock, credentials: HueBridgeCredentials
    ) -> None:
        with pytest.raises(ValueError, match="frames per second"):
            make_stream(areas, credentials, rate=MAX_RATE + 1)
        with pytest.raises(ValueError, match="frames per second"):
            make_stream(areas, credentials, rate=0)

    @pytest.mark.asyncio
    async def test_starts_the_area_before_handshaking(
        self,
        areas: AsyncMock,
        credentials: HueBridgeCredentials,
        connection: FakeConnection,
        dtls: FakeDtls,
    ) -> None:
        async with make_stream(areas, credentials):
            pass

        areas.start.assert_awaited_once_with(AREA_ID)
        assert connection.connected_to == (BRIDGE_IP, APP_KEY, CLIENT_KEY)

    @pytest.mark.asyncio
    async def test_reads_an_area_that_was_given_by_id(
        self,
        areas: AsyncMock,
        credentials: HueBridgeCredentials,
        dtls: FakeDtls,
    ) -> None:
        async with make_stream(areas, credentials, area=AREA_ID) as stream:
            assert stream.area.id == AREA_ID

        areas.get_one.assert_awaited_once_with(AREA_ID)

    @pytest.mark.asyncio
    async def test_gives_the_area_back_when_the_handshake_fails(
        self,
        areas: AsyncMock,
        credentials: HueBridgeCredentials,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        class Refusing:
            async def connect(self, *args: object) -> object:
                raise EntertainmentError("no answer")

        monkeypatch.setattr(
            "hueify.entertainment.stream._dtls_connection", lambda: Refusing()
        )

        with pytest.raises(EntertainmentError, match="no answer"):
            await make_stream(areas, credentials).open()

        areas.start.assert_awaited_once()
        areas.stop.assert_awaited_once_with(AREA_ID)

    @pytest.mark.asyncio
    async def test_says_which_extra_is_missing(
        self,
        areas: AsyncMock,
        credentials: HueBridgeCredentials,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setitem(sys.modules, "hueify.entertainment.dtls", None)

        with pytest.raises(MissingDependencyError, match=r"hueify\[entertainment\]"):
            await make_stream(areas, credentials).open()

        areas.start.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_opening_twice_keeps_the_one_session(
        self, areas: AsyncMock, credentials: HueBridgeCredentials, dtls: FakeDtls
    ) -> None:
        stream = make_stream(areas, credentials)
        await stream.open()
        try:
            await stream.open()
        finally:
            await stream.close()

        areas.start.assert_awaited_once()

    def test_the_frame_is_not_there_before_the_stream_is_open(
        self, areas: AsyncMock, credentials: HueBridgeCredentials
    ) -> None:
        stream = make_stream(areas, credentials)

        with pytest.raises(EntertainmentError, match="not open"):
            stream.set_all("red")
        with pytest.raises(EntertainmentError, match="not open"):
            _ = stream.channels


class TestSending:
    @pytest.mark.asyncio
    async def test_sends_frames_of_the_area_on_its_own(
        self,
        areas: AsyncMock,
        credentials: HueBridgeCredentials,
        connection: FakeConnection,
        dtls: FakeDtls,
    ) -> None:
        async with make_stream(areas, credentials) as stream:
            stream.set_all("red")
            await asyncio.sleep(0.15)

        assert 2 <= len(connection.sent) <= 30
        assert {len(frame) for frame in connection.sent} == {frame_length(2)}
        assert stream.stats.frames_sent == len(connection.sent)

    @pytest.mark.asyncio
    async def test_the_first_frame_carries_the_colors_set_after_opening(
        self,
        areas: AsyncMock,
        credentials: HueBridgeCredentials,
        connection: FakeConnection,
        dtls: FakeDtls,
    ) -> None:
        """Nothing is sent before the caller has had a chance to paint."""
        async with make_stream(areas, credentials) as stream:
            stream.set_all("red")
            await asyncio.sleep(0.05)

        assert connection.sent
        assert connection.sent[0][CHANNELS_AT:] == (
            b"\x00\xff\xff\x00\x00\x00\x00\x01\xff\xff\x00\x00\x00\x00"
        )

    @pytest.mark.asyncio
    async def test_keeps_resending_the_last_frame_so_the_area_stays_alive(
        self,
        areas: AsyncMock,
        credentials: HueBridgeCredentials,
        connection: FakeConnection,
        dtls: FakeDtls,
    ) -> None:
        async with make_stream(areas, credentials) as stream:
            stream.set_all("red")
            await asyncio.sleep(0.1)

        colors = {frame[CHANNELS_AT:] for frame in connection.sent}
        sequences = [frame[SEQUENCE_BYTE] for frame in connection.sent]

        assert len(colors) == 1
        assert sequences == sorted(sequences)
        assert len(set(sequences)) == len(sequences)

    @pytest.mark.asyncio
    async def test_a_write_is_never_split_across_two_frames(
        self,
        areas: AsyncMock,
        credentials: HueBridgeCredentials,
        connection: FakeConnection,
        dtls: FakeDtls,
    ) -> None:
        async with make_stream(areas, credentials) as stream:
            for _ in range(10):
                stream.set(0, "red")
                stream.set(1, "red")
                await asyncio.sleep(0.01)
                stream.set(0, "blue")
                stream.set(1, "blue")
                await asyncio.sleep(0.01)

        for frame in connection.sent:
            first, second = frame[CHANNELS_AT:][1:7], frame[CHANNELS_AT:][8:14]
            assert first == second


class TestSources:
    @pytest.mark.asyncio
    async def test_a_source_paints_every_frame_on_a_rising_clock(
        self,
        areas: AsyncMock,
        credentials: HueBridgeCredentials,
        connection: FakeConnection,
        dtls: FakeDtls,
    ) -> None:
        ticks: list[Tick] = []

        def render(frame: object, tick: Tick) -> None:
            ticks.append(tick)

        async with make_stream(areas, credentials) as stream:
            running = asyncio.create_task(stream.run(render))
            await asyncio.sleep(0.1)
            running.cancel()

        assert [tick.index for tick in ticks] == list(range(len(ticks)))
        assert [tick.elapsed for tick in ticks] == sorted(
            tick.elapsed for tick in ticks
        )
        assert all(tick.delta > 0 for tick in ticks[1:])

    @pytest.mark.asyncio
    async def test_an_object_with_a_render_method_is_a_source_too(
        self,
        areas: AsyncMock,
        credentials: HueBridgeCredentials,
        connection: FakeConnection,
        dtls: FakeDtls,
    ) -> None:
        class Pulse:
            def render(self, frame, tick: Tick) -> None:
                frame.set_all("white", brightness=0.5)

        async with make_stream(areas, credentials) as stream:
            running = asyncio.create_task(stream.run(Pulse()))
            await asyncio.sleep(0.05)
            running.cancel()

        assert connection.sent
        assert connection.sent[-1][CHANNELS_AT:][1:3] == b"\x80\x00"

    @pytest.mark.asyncio
    async def test_a_source_that_raises_stops_the_stream_and_says_why(
        self,
        areas: AsyncMock,
        credentials: HueBridgeCredentials,
        dtls: FakeDtls,
    ) -> None:
        def broken(frame: object, tick: Tick) -> None:
            raise ZeroDivisionError("bad envelope")

        async with make_stream(areas, credentials) as stream:
            with pytest.raises(ZeroDivisionError, match="bad envelope"):
                await stream.run(broken)

            assert not stream.sending
            assert isinstance(stream.error, ZeroDivisionError)


class TestFailures:
    @pytest.mark.asyncio
    async def test_a_broken_connection_surfaces_where_it_is_awaited(
        self,
        areas: AsyncMock,
        credentials: HueBridgeCredentials,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        failing = FakeConnection(fail_on_send=EntertainmentError("stream gone"))
        FakeDtls(failing).install(monkeypatch)

        async with make_stream(areas, credentials) as stream:
            with pytest.raises(EntertainmentError, match="stream gone"):
                await stream.wait_closed()

            assert isinstance(stream.error, EntertainmentError)

    @pytest.mark.asyncio
    async def test_closing_gives_the_area_back_and_closes_the_socket(
        self,
        areas: AsyncMock,
        credentials: HueBridgeCredentials,
        connection: FakeConnection,
        dtls: FakeDtls,
    ) -> None:
        stream = make_stream(areas, credentials)
        await stream.open()

        await stream.close()

        assert not stream.sending
        assert connection.closed
        areas.stop.assert_awaited_once_with(AREA_ID)

    @pytest.mark.asyncio
    async def test_an_area_the_bridge_already_took_away_still_closes(
        self,
        areas: AsyncMock,
        credentials: HueBridgeCredentials,
        connection: FakeConnection,
        dtls: FakeDtls,
    ) -> None:
        areas.stop.side_effect = EntertainmentError("not streaming")

        async with make_stream(areas, credentials):
            pass

        assert connection.closed

    @pytest.mark.asyncio
    async def test_waiting_on_a_stream_that_was_never_opened_returns(
        self, areas: AsyncMock, credentials: HueBridgeCredentials
    ) -> None:
        await make_stream(areas, credentials).wait_closed()


class TestGeometry:
    @pytest.mark.asyncio
    async def test_channels_come_with_the_positions_of_the_area(
        self,
        areas: AsyncMock,
        credentials: HueBridgeCredentials,
        dtls: FakeDtls,
    ) -> None:
        async with make_stream(areas, credentials) as stream:
            channels = stream.channels

        assert [channel.channel_id for channel in channels] == [0, 1]
        assert channels[0].position.x == -1.0
        assert channels[1].position.z == 0.5
