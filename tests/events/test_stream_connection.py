import asyncio

import pytest

from hueify.sse.connection import ConnectionStatus, StreamConnection


class TestState:
    def test_starts_disconnected(self) -> None:
        connection = StreamConnection()

        assert connection.connected is False
        assert connection.last_event_at is None

    @pytest.mark.asyncio
    async def test_since_marks_the_start_of_the_current_state(self) -> None:
        connection = StreamConnection()
        disconnected_since = connection.since

        await connection.opened()

        assert connection.since > disconnected_since

    @pytest.mark.asyncio
    async def test_record_event_timestamps_the_last_sign_of_life(self) -> None:
        connection = StreamConnection()

        connection.record_event()

        assert connection.last_event_at is not None


class TestNotifications:
    @pytest.mark.asyncio
    async def test_handler_is_called_on_connect_and_disconnect(self) -> None:
        connection = StreamConnection()
        seen: list[ConnectionStatus] = []
        connection.on_change(lambda status: _record(seen, status))

        await connection.opened()
        await connection.closed()

        assert [status.connected for status in seen] == [True, False]

    @pytest.mark.asyncio
    async def test_repeated_state_does_not_notify_again(self) -> None:
        connection = StreamConnection()
        seen: list[ConnectionStatus] = []
        connection.on_change(lambda status: _record(seen, status))

        await connection.opened()
        await connection.opened()
        await connection.closed()
        await connection.closed()

        assert len(seen) == 2

    @pytest.mark.asyncio
    async def test_off_change_stops_notifications(self) -> None:
        connection = StreamConnection()
        seen: list[ConnectionStatus] = []

        def handler(status: ConnectionStatus):
            return _record(seen, status)

        connection.on_change(handler)
        connection.off_change(handler)
        await connection.opened()

        assert seen == []

    @pytest.mark.asyncio
    async def test_a_failing_handler_does_not_affect_the_others(self) -> None:
        connection = StreamConnection()
        seen: list[ConnectionStatus] = []

        async def failing(status: ConnectionStatus) -> None:
            raise RuntimeError("handler exploded")

        connection.on_change(failing)
        connection.on_change(lambda status: _record(seen, status))

        await connection.opened()

        assert len(seen) == 1


class TestWaitConnected:
    @pytest.mark.asyncio
    async def test_returns_false_when_the_connection_never_opens(self) -> None:
        connection = StreamConnection()

        assert await connection.wait_connected(timeout=0.01) is False

    @pytest.mark.asyncio
    async def test_returns_true_once_the_connection_opens(self) -> None:
        connection = StreamConnection()
        waiting = asyncio.create_task(connection.wait_connected(timeout=1))
        await asyncio.sleep(0)

        await connection.opened()

        assert await waiting is True

    @pytest.mark.asyncio
    async def test_waits_again_after_the_connection_drops(self) -> None:
        connection = StreamConnection()
        await connection.opened()
        await connection.closed()

        assert await connection.wait_connected(timeout=0.01) is False


async def _record(seen: list[ConnectionStatus], status: ConnectionStatus) -> None:
    seen.append(status)
