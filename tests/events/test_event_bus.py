from unittest.mock import AsyncMock

import pytest
from pydantic import BaseModel

from hueify.sse import EventBus


class LightChanged(BaseModel):
    light_id: str
    brightness: float


class TemperatureChanged(BaseModel):
    mirek: int


class TestSubscribe:
    @pytest.mark.asyncio
    async def test_registered_handler_is_called_on_dispatch(self) -> None:
        bus = EventBus()
        handler = AsyncMock()
        event = LightChanged(light_id="abc", brightness=80.0)

        bus.subscribe(LightChanged, handler)
        await bus.dispatch(event)

        handler.assert_called_once_with(event)

    @pytest.mark.asyncio
    async def test_multiple_handlers_are_all_called(self) -> None:
        bus = EventBus()
        handler_a = AsyncMock()
        handler_b = AsyncMock()
        event = LightChanged(light_id="abc", brightness=50.0)

        bus.subscribe(LightChanged, handler_a)
        bus.subscribe(LightChanged, handler_b)
        await bus.dispatch(event)

        handler_a.assert_called_once_with(event)
        handler_b.assert_called_once_with(event)

    @pytest.mark.asyncio
    async def test_handler_only_receives_its_subscribed_event_type(self) -> None:
        bus = EventBus()
        light_handler = AsyncMock()
        temp_handler = AsyncMock()

        bus.subscribe(LightChanged, light_handler)
        bus.subscribe(TemperatureChanged, temp_handler)

        await bus.dispatch(LightChanged(light_id="abc", brightness=50.0))

        light_handler.assert_called_once()
        temp_handler.assert_not_called()


class TestUnsubscribe:
    @pytest.mark.asyncio
    async def test_unsubscribed_handler_is_not_called(self) -> None:
        bus = EventBus()
        handler = AsyncMock()
        event = LightChanged(light_id="abc", brightness=80.0)

        bus.subscribe(LightChanged, handler)
        bus.unsubscribe(LightChanged, handler)
        await bus.dispatch(event)

        handler.assert_not_called()

    def test_unsubscribe_unknown_event_type_does_not_raise(self) -> None:
        bus = EventBus()
        handler = AsyncMock()
        bus.unsubscribe(LightChanged, handler)

    def test_unsubscribe_unregistered_handler_does_not_raise(self) -> None:
        bus = EventBus()
        handler_a = AsyncMock()
        handler_b = AsyncMock()

        bus.subscribe(LightChanged, handler_a)
        bus.unsubscribe(LightChanged, handler_b)


class TestDispatch:
    @pytest.mark.asyncio
    async def test_returns_dispatched_event(self) -> None:
        bus = EventBus()
        event = LightChanged(light_id="abc", brightness=80.0)

        result = await bus.dispatch(event)

        assert result is event

    @pytest.mark.asyncio
    async def test_returns_event_when_no_handlers_registered(self) -> None:
        bus = EventBus()
        event = LightChanged(light_id="abc", brightness=80.0)

        result = await bus.dispatch(event)

        assert result is event

    @pytest.mark.asyncio
    async def test_continues_dispatching_when_one_handler_raises(self) -> None:
        bus = EventBus()
        failing_handler = AsyncMock(side_effect=RuntimeError("boom"))
        succeeding_handler = AsyncMock()
        event = LightChanged(light_id="abc", brightness=80.0)

        bus.subscribe(LightChanged, failing_handler)
        bus.subscribe(LightChanged, succeeding_handler)
        await bus.dispatch(event)

        succeeding_handler.assert_called_once_with(event)

    @pytest.mark.asyncio
    async def test_handlers_are_called_concurrently(self) -> None:
        import asyncio

        bus = EventBus()
        call_order: list[str] = []

        async def slow_handler(event: LightChanged) -> None:
            await asyncio.sleep(0.05)
            call_order.append("slow")

        async def fast_handler(event: LightChanged) -> None:
            call_order.append("fast")

        bus.subscribe(LightChanged, slow_handler)
        bus.subscribe(LightChanged, fast_handler)
        await bus.dispatch(LightChanged(light_id="abc", brightness=50.0))

        assert "fast" in call_order
        assert "slow" in call_order
