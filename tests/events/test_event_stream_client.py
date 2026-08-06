import asyncio
import time
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from hueify.credentials import HueBridgeCredentials
from hueify.errors import StreamAuthenticationError
from hueify.models import LightEvent, ResourceType
from hueify.sse import ConnectionStatus, EventStream, ReconnectPolicy

# Keeps the supervisor's backoff below a millisecond so tests stay fast.
INSTANT_RETRY = ReconnectPolicy(initial_backoff=0.001, max_backoff=0.001)


class _FakeClock:
    """Replays fixed `time.monotonic()` readings so "healthy" uptime can be
    simulated without the test actually waiting for it."""

    def __init__(self, readings: list[float]) -> None:
        self._readings = readings
        self._index = 0

    def __call__(self) -> float:
        reading = self._readings[min(self._index, len(self._readings) - 1)]
        self._index += 1
        return reading


class _FakeModule:
    """Delegates to a real module except for the overridden attributes.

    Patching `time.monotonic` or `asyncio.sleep` directly would corrupt
    asyncio's own event-loop clock, since the loop also reads them. Swapping
    the whole `time`/`asyncio` name inside `client.py`'s namespace for one of
    these keeps the fake confined to the module under test.
    """

    def __init__(self, real_module: object, **overrides: object) -> None:
        self._real_module = real_module
        self._overrides = overrides

    def __getattr__(self, name: str) -> object:
        if name in self._overrides:
            return self._overrides[name]
        return getattr(self._real_module, name)


def make_events(policy: ReconnectPolicy | None = None) -> EventStream:
    credentials = HueBridgeCredentials(
        hue_bridge_ip="192.168.1.1",
        hue_app_key="a" * 20,
    )
    return EventStream(credentials, policy)


def make_light_event() -> LightEvent:
    return LightEvent(
        id="00000000-0000-0000-0000-000000000001",
        type=ResourceType.LIGHT,
    )


async def never_returns() -> None:
    await asyncio.Event().wait()


class TestConnectionAccessors:
    @pytest.mark.asyncio
    async def test_status_reflects_the_underlying_connection(self) -> None:
        events = make_events()

        await events._connection.opened()

        assert events.status.connected is True
        await events.stop()

    @pytest.mark.asyncio
    async def test_last_event_at_reflects_the_underlying_connection(self) -> None:
        events = make_events()

        events._connection.record_event()

        assert events.last_event_at is not None
        await events.stop()

    @pytest.mark.asyncio
    async def test_off_connection_change_stops_notifications(self) -> None:
        events = make_events()
        seen: list[ConnectionStatus] = []

        def handler(status: ConnectionStatus) -> None:
            seen.append(status)

        events.on_connection_change(handler)
        events.off_connection_change(handler)

        await events._connection.opened()

        assert seen == []
        await events.stop()


class TestHandlers:
    @pytest.mark.asyncio
    async def test_on_can_be_used_as_typed_decorator(self) -> None:
        events = make_events()
        received: list[LightEvent] = []

        @events.on(ResourceType.LIGHT)
        async def on_light(event: LightEvent) -> None:
            received.append(event)

        event = make_light_event()
        await events._bus.dispatch(event)

        assert received == [event]
        await events.stop()

    @pytest.mark.asyncio
    async def test_off_stops_further_dispatches_to_the_handler(self) -> None:
        events = make_events()
        received: list[LightEvent] = []

        async def on_light(event: LightEvent) -> None:
            received.append(event)

        events.on(ResourceType.LIGHT, on_light)
        events.off(ResourceType.LIGHT, on_light)

        await events._bus.dispatch(make_light_event())

        assert received == []
        await events.stop()


class TestLifecycle:
    @pytest.mark.asyncio
    async def test_starting_twice_is_a_harmless_no_op(self) -> None:
        events = make_events()

        with patch.object(
            events._stream, "run_once", new=AsyncMock(side_effect=never_returns)
        ) as run_once:
            await events.start()
            first_task = events._task

            await events.start()

            assert events._task is first_task
            run_once.assert_awaited_once()
            await events.stop()

    @pytest.mark.asyncio
    async def test_start_is_explicit_and_runs_in_background(self) -> None:
        events = make_events()

        with patch.object(
            events._stream, "run_once", new=AsyncMock(side_effect=never_returns)
        ):
            assert events.running is False

            await events.start()

            assert events.running is True
            await events.stop()

        assert events.running is False

    @pytest.mark.asyncio
    async def test_stop_leaves_the_stream_disconnected(self) -> None:
        events = make_events()

        async def stay_connected() -> None:
            await events._connection.opened()
            await never_returns()

        with patch.object(
            events._stream, "run_once", new=AsyncMock(side_effect=stay_connected)
        ):
            await events.start()
            await events.wait_connected(timeout=1)

            await events.stop()

        assert events.connected is False
        assert events.running is False

    @pytest.mark.asyncio
    async def test_wait_connected_times_out_while_the_bridge_is_unreachable(
        self,
    ) -> None:
        events = make_events(INSTANT_RETRY)

        with patch.object(
            events._stream,
            "run_once",
            new=AsyncMock(side_effect=httpx.ConnectError("refused")),
        ):
            await events.start()

            assert await events.wait_connected(timeout=0.05) is False
            await events.stop()


class TestStartWithTimeout:
    @pytest.mark.asyncio
    async def test_returns_once_the_connection_is_open(self) -> None:
        events = make_events()

        async def stay_connected() -> None:
            await events._connection.opened()
            await never_returns()

        with patch.object(
            events._stream, "run_once", new=AsyncMock(side_effect=stay_connected)
        ):
            await events.start(timeout=1)

            assert events.connected is True
            await events.stop()

    @pytest.mark.asyncio
    async def test_raises_when_the_bridge_stays_unreachable(self) -> None:
        events = make_events(INSTANT_RETRY)

        with patch.object(
            events._stream, "run_once", new=AsyncMock(side_effect=never_returns)
        ):
            with pytest.raises(TimeoutError):
                await events.start(timeout=0.05)

            # Waiting in vain does not stop the stream from trying.
            assert events.running is True
            await events.stop()

    @pytest.mark.asyncio
    async def test_reports_the_real_cause_instead_of_a_bare_timeout(self) -> None:
        events = make_events(INSTANT_RETRY)
        error = StreamAuthenticationError("rejected")

        with patch.object(events._stream, "run_once", new=AsyncMock(side_effect=error)):
            with pytest.raises(StreamAuthenticationError):
                await events.start(timeout=0.2)

            await events.stop()


class TestReconnecting:
    @pytest.mark.asyncio
    async def test_retries_until_the_bridge_accepts_the_connection(self) -> None:
        events = make_events(INSTANT_RETRY)
        attempts = 0

        async def flaky() -> None:
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                raise httpx.ConnectError("refused")
            await events._connection.opened()
            await never_returns()

        with patch.object(events._stream, "run_once", new=AsyncMock(side_effect=flaky)):
            await events.start()

            assert await events.wait_connected(timeout=1) is True
            assert attempts == 3
            await events.stop()

    @pytest.mark.asyncio
    async def test_reconnects_after_the_bridge_closes_the_stream(self) -> None:
        events = make_events(INSTANT_RETRY)
        reconnected = asyncio.Event()
        attempts = 0

        async def close_then_stay() -> None:
            nonlocal attempts
            attempts += 1
            if attempts > 1:
                reconnected.set()
                await never_returns()

        with patch.object(
            events._stream, "run_once", new=AsyncMock(side_effect=close_then_stay)
        ):
            await events.start()

            await asyncio.wait_for(reconnected.wait(), timeout=1)
            await events.stop()

    @pytest.mark.asyncio
    async def test_an_idle_timeout_is_treated_as_a_plain_reconnect(self) -> None:
        events = make_events(INSTANT_RETRY)
        reconnected = asyncio.Event()
        attempts = 0

        async def time_out_once() -> None:
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                raise httpx.ReadTimeout("no data")
            reconnected.set()
            await never_returns()

        with patch.object(
            events._stream, "run_once", new=AsyncMock(side_effect=time_out_once)
        ):
            await events.start()

            await asyncio.wait_for(reconnected.wait(), timeout=1)
            assert events.last_error is None
            await events.stop()

    @pytest.mark.asyncio
    async def test_notifies_handlers_about_loss_and_recovery(self) -> None:
        events = make_events(INSTANT_RETRY)
        seen: list[ConnectionStatus] = []
        recovered = asyncio.Event()
        attempts = 0

        @events.on_connection_change
        async def on_change(status: ConnectionStatus) -> None:
            seen.append(status)

        async def drop_once() -> None:
            nonlocal attempts
            attempts += 1
            await events._connection.opened()
            if attempts == 1:
                raise httpx.ReadError("connection reset")
            recovered.set()
            await never_returns()

        with patch.object(
            events._stream, "run_once", new=AsyncMock(side_effect=drop_once)
        ):
            await events.start()

            await asyncio.wait_for(recovered.wait(), timeout=1)
            await events.stop()

        # Connected, lost, back again - and a final loss when the stream stops.
        assert [status.connected for status in seen] == [True, False, True, False]

    @pytest.mark.asyncio
    async def test_keeps_the_last_error_for_diagnostics(self) -> None:
        events = make_events(INSTANT_RETRY)
        failed = asyncio.Event()

        async def fail_then_stay() -> None:
            if not failed.is_set():
                failed.set()
                raise httpx.ConnectError("refused")
            await never_returns()

        with patch.object(
            events._stream, "run_once", new=AsyncMock(side_effect=fail_then_stay)
        ):
            await events.start()
            await asyncio.wait_for(failed.wait(), timeout=1)
            await events.stop()

        assert isinstance(events.last_error, httpx.ConnectError)

    @pytest.mark.asyncio
    async def test_clears_the_last_error_after_recovery(self) -> None:
        events = make_events(INSTANT_RETRY)
        attempts = 0

        async def fail_then_recover() -> None:
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                raise httpx.ConnectError("refused")
            await events._connection.opened()
            await never_returns()

        with patch.object(
            events._stream, "run_once", new=AsyncMock(side_effect=fail_then_recover)
        ):
            await events.start()
            assert await events.wait_connected(timeout=1) is True
            assert events.last_error is None
            await events.stop()


class TestBackoffReset:
    @pytest.mark.asyncio
    async def test_resets_backoff_after_a_healthy_connection(self) -> None:
        # Two quick failures climb the backoff ladder, a third connection is
        # "healthy" long enough to reset it, and a fourth failure should see
        # the delay drop back down instead of continuing to climb.
        policy = ReconnectPolicy(
            initial_backoff=0.01,
            max_backoff=1.0,
            backoff_factor=10.0,
            healthy_after=0.05,
        )
        events = make_events(policy)
        attempts = 0
        delays: list[float] = []
        real_sleep = asyncio.sleep
        reached_fourth_attempt = asyncio.Event()

        async def flaky() -> None:
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                raise httpx.ConnectError("refused")
            if attempts == 3:
                raise httpx.ReadError("reset")
            reached_fourth_attempt.set()
            await never_returns()

        async def recording_sleep(delay: float) -> None:
            # `start()` also yields via `asyncio.sleep(0)` - only the
            # supervisor's backoff delays are of interest here.
            if delay > 0:
                delays.append(delay)
            await real_sleep(0)

        clock = _FakeClock(
            [
                0,
                0.001,  # attempt 1: 0.001s elapsed - not healthy
                1,
                1.001,  # attempt 2: 0.001s elapsed - not healthy
                2,
                102,  # attempt 3: 100s elapsed - healthy, backoff resets
                100,  # attempt 4: started
            ]
        )

        fake_time = _FakeModule(time, monotonic=clock)
        fake_asyncio = _FakeModule(asyncio, sleep=recording_sleep)

        with (
            patch.object(events._stream, "run_once", new=AsyncMock(side_effect=flaky)),
            patch("hueify.sse.client.time", new=fake_time),
            patch("hueify.sse.client.asyncio", new=fake_asyncio),
        ):
            await events.start()
            await asyncio.wait_for(reached_fourth_attempt.wait(), timeout=1)
            await events.stop()

        # Attempt 2 climbed the ladder; attempt 3 (post-reset) drops back down
        # to the shortest delay instead of climbing further.
        assert len(delays) == 3
        assert delays[2] < delays[1]
        assert delays[2] <= policy.initial_backoff


class TestGivingUp:
    @pytest.mark.asyncio
    async def test_stops_retrying_when_the_bridge_rejects_the_key(self) -> None:
        events = make_events(INSTANT_RETRY)
        error = StreamAuthenticationError("rejected")

        with patch.object(
            events._stream, "run_once", new=AsyncMock(side_effect=error)
        ) as run_once:
            await events.start()
            await asyncio.wait_for(asyncio.shield(events._task), timeout=1)

            assert events.running is False
            assert events.last_error is error
            assert run_once.await_count == 1
            await events.stop()

    @pytest.mark.asyncio
    async def test_an_unexpected_error_stops_the_supervisor_visibly(self) -> None:
        events = make_events(INSTANT_RETRY)

        with patch.object(
            events._stream, "run_once", new=AsyncMock(side_effect=RuntimeError("bug"))
        ):
            await events.start()
            await asyncio.wait_for(asyncio.shield(events._task), timeout=1)

            assert events.running is False
            assert isinstance(events.last_error, RuntimeError)
            assert events.connected is False
            await events.stop()
