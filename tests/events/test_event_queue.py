import asyncio
import contextlib
import json
from unittest.mock import AsyncMock, patch
from uuid import UUID

import httpx
import pytest
from httpx_sse import ServerSentEvent

from hueify.credentials import HueBridgeCredentials
from hueify.models import LightEvent
from hueify.sse import EventStream, ReconnectPolicy
from hueify.sse.bus import EventBus
from hueify.sse.queue import EventQueue


def event(number: int) -> LightEvent:
    return LightEvent(id=UUID(int=number))


def events_client() -> EventStream:
    return EventStream(
        HueBridgeCredentials(HUE_BRIDGE_IP="192.168.1.1", HUE_APP_KEY="a" * 20),
        ReconnectPolicy(initial_backoff=0.001, max_backoff=0.001),
        queue_size=4,
    )


@pytest.mark.parametrize("capacity", [0, -1, 1.5, True])
def test_queue_requires_a_positive_integer_capacity(capacity):
    with pytest.raises(ValueError, match="positive integer"):
        EventQueue(EventBus(), capacity)


@pytest.mark.asyncio
async def test_full_queue_waits_without_dropping_events(caplog):
    bus = AsyncMock(spec=EventBus)
    queue = EventQueue(bus, capacity=1)
    await queue.dispatch(event(1))
    blocked = asyncio.create_task(queue.dispatch(event(2)))
    worker = None
    try:
        await asyncio.sleep(0)
        assert not blocked.done()
        assert queue.pending == 1
        assert "queue is full" in caplog.text
        worker = asyncio.create_task(queue.run())
        async with asyncio.timeout(1):
            await blocked
            await queue._queue.join()
        assert [call.args[0].id.int for call in bus.dispatch.await_args_list] == [1, 2]
    finally:
        blocked.cancel()
        await asyncio.gather(blocked, return_exceptions=True)
        if worker is not None:
            worker.cancel()
            await asyncio.gather(worker, return_exceptions=True)


@pytest.mark.asyncio
async def test_slow_handlers_do_not_block_receiving_and_stop_clears_the_queue():
    client = events_client()
    entered = asyncio.Event()
    received = asyncio.Event()
    cancelled = asyncio.Event()
    calls: list[int] = []

    @client.on("light")
    async def slow(changed):
        calls.append(changed.id.int)
        entered.set()
        try:
            await asyncio.Event().wait()
        finally:
            cancelled.set()

    async def receive():
        await client._stream._handle_sse(
            ServerSentEvent(
                data=json.dumps(
                    [
                        {
                            "data": [
                                event(number).model_dump(mode="json")
                                for number in (1, 2, 3)
                            ]
                        }
                    ]
                )
            )
        )
        received.set()
        await asyncio.Event().wait()

    with patch.object(client._stream, "run_once", side_effect=receive):
        try:
            await client.start()
            async with asyncio.timeout(1):
                await entered.wait()
                await received.wait()
            assert client.pending_events == 2
        finally:
            async with asyncio.timeout(1):
                await client.stop()
    assert cancelled.is_set()
    assert client.pending_events == 0
    assert calls == [1]

    restarted = asyncio.Event()

    async def idle_connection():
        restarted.set()
        await asyncio.Event().wait()

    with patch.object(client._stream, "run_once", side_effect=idle_connection):
        try:
            await client.start()
            async with asyncio.timeout(1):
                await restarted.wait()
            assert calls == [1]
        finally:
            await client.stop()


@pytest.mark.asyncio
async def test_queued_events_survive_reconnect_and_wait_for_prior_handlers():
    client = events_client()
    entered = asyncio.Event()
    recovered = asyncio.Event()
    release = asyncio.Event()
    completed = asyncio.Event()
    seen: list[int] = []
    attempts = 0

    @client.on("light")
    async def slow(changed):
        seen.append(changed.id.int)
        if changed.id.int == 1:
            entered.set()
            await release.wait()
        else:
            completed.set()

    async def reconnect():
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            await client._queue.dispatch(event(1))
            await client._queue.dispatch(event(2))
            raise httpx.ConnectError("connection lost")
        recovered.set()
        await asyncio.Event().wait()

    with patch.object(client._stream, "run_once", side_effect=reconnect):
        try:
            await client.start()
            async with asyncio.timeout(1):
                await entered.wait()
                await recovered.wait()
                assert seen == [1]
                assert client.pending_events == 1
                release.set()
                await completed.wait()
            assert seen == [1, 2]
        finally:
            await client.stop()


@pytest.mark.asyncio
async def test_dispatch_failure_does_not_stop_later_events():
    bus = AsyncMock(spec=EventBus)
    bus.dispatch.side_effect = [RuntimeError("broken handler"), None]
    queue = EventQueue(bus, capacity=2)
    await queue.dispatch(event(1))
    await queue.dispatch(event(2))
    worker = asyncio.create_task(queue.run())
    try:
        async with asyncio.timeout(1):
            await queue._queue.join()
        assert bus.dispatch.await_count == 2
    finally:
        worker.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await worker


@pytest.mark.asyncio
@pytest.mark.parametrize("callback", ["event", "connected", "disconnected", "child"])
async def test_callbacks_can_request_shutdown_without_waiting_on_themselves(callback):
    client = events_client()
    requested = asyncio.Event()

    async def stop():
        if callback == "child":
            await asyncio.create_task(client.stop())
        else:
            await client.stop()
        requested.set()

    @client.on("light")
    async def on_event(changed):
        if callback in {"event", "child"}:
            await stop()

    @client.on_connection_change
    async def on_connection(status):
        if (callback == "connected" and status.connected) or (
            callback == "disconnected" and not status.connected
        ):
            await stop()

    async def receive():
        await client._connection.opened()
        if callback == "disconnected":
            raise httpx.ReadError("lost connection")
        await client._queue.dispatch(event(1))
        await asyncio.Event().wait()

    with patch.object(client._stream, "run_once", side_effect=receive):
        try:
            await client.start()
            async with asyncio.timeout(1):
                await requested.wait()
                await client.stop()
        finally:
            await client.stop()
    assert not client.running
    assert not client.connected
    assert client.pending_events == 0


@pytest.mark.asyncio
async def test_recovery_resync_follows_old_events_even_when_a_handler_waits_for_connection():
    client = events_client()
    entered = asyncio.Event()
    disconnected = asyncio.Event()
    resynced = asyncio.Event()
    order: list[str] = []
    state = {"on": None}
    attempts = 0

    @client.on("light")
    async def on_event(changed):
        if changed.id.int == 1:
            entered.set()
            await disconnected.wait()
            assert await client.wait_connected(timeout=1)
        state["on"] = False
        order.append(f"event-{changed.id.int}")

    @client.on_connection_change
    async def on_connection(status):
        if not status.connected:
            disconnected.set()
        elif attempts == 2:
            state["on"] = True
            order.append("resync")
            resynced.set()

    async def receive():
        nonlocal attempts
        attempts += 1
        await client._connection.opened()
        if attempts == 1:
            await client._queue.dispatch(event(1))
            await client._queue.dispatch(event(2))
            await entered.wait()
            raise httpx.ReadError("lost connection")
        await asyncio.Event().wait()

    with patch.object(client._stream, "run_once", side_effect=receive):
        try:
            await client.start()
            async with asyncio.timeout(1):
                await resynced.wait()
            assert order == ["event-1", "event-2", "resync"]
            assert state["on"] is True
        finally:
            await client.stop()


@pytest.mark.asyncio
async def test_background_task_outliving_its_callback_waits_for_shutdown():
    client = events_client()
    release = asyncio.Event()
    background = None

    async def stop_later():
        await release.wait()
        await client.stop()
        assert not client.running

    @client.on("light")
    async def on_event(changed):
        nonlocal background
        background = asyncio.create_task(stop_later())

    async def receive():
        await client._queue.dispatch(event(1))
        await asyncio.Event().wait()

    with patch.object(client._stream, "run_once", side_effect=receive):
        try:
            await client.start()
            async with asyncio.timeout(1):
                await client._queue.join()
                assert background is not None
                release.set()
                await background
        finally:
            if background is not None:
                background.cancel()
                await asyncio.gather(background, return_exceptions=True)
            await client.stop()


@pytest.mark.asyncio
async def test_concurrent_stop_calls_do_not_interrupt_handler_cleanup():
    client = events_client()
    entered = asyncio.Event()
    cleaned = asyncio.Event()

    @client.on("light")
    async def on_event(changed):
        entered.set()
        try:
            await asyncio.Event().wait()
        finally:
            await asyncio.sleep(0)
            cleaned.set()

    async def receive():
        await client._queue.dispatch(event(1))
        await asyncio.Event().wait()

    with patch.object(client._stream, "run_once", side_effect=receive):
        try:
            await client.start()
            async with asyncio.timeout(1):
                await entered.wait()
                await asyncio.gather(client.stop(), client.stop())
            assert cleaned.is_set()
            assert not client.running
        finally:
            await client.stop()


@pytest.mark.asyncio
async def test_cancelling_a_stop_waiter_does_not_cancel_shared_cleanup():
    client = events_client()
    entered = asyncio.Event()
    cleaning = asyncio.Event()
    release = asyncio.Event()
    cleaned = asyncio.Event()

    @client.on("light")
    async def on_event(changed):
        entered.set()
        try:
            await asyncio.Event().wait()
        finally:
            cleaning.set()
            await release.wait()
            cleaned.set()

    async def receive():
        await client._queue.dispatch(event(1))
        await asyncio.Event().wait()

    waiter = None
    with patch.object(client._stream, "run_once", side_effect=receive):
        try:
            await client.start()
            async with asyncio.timeout(1):
                await entered.wait()
                waiter = asyncio.create_task(client.stop())
                await cleaning.wait()
                waiter.cancel()
                with pytest.raises(asyncio.CancelledError):
                    await waiter
                assert client.running
                release.set()
                await client.stop()
            assert cleaned.is_set()
        finally:
            release.set()
            if waiter is not None:
                waiter.cancel()
                await asyncio.gather(waiter, return_exceptions=True)
            await client.stop()
