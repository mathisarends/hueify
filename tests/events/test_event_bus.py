import asyncio
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from hueify.models import LightEvent, ResourceType, SceneEvent
from hueify.sse import EventBus


def light_event(brightness: float = 80.0) -> LightEvent:
    return LightEvent(
        id=uuid4(),
        type=ResourceType.LIGHT,
        dimming={"brightness": brightness},
    )


class TestSubscribe:
    @pytest.mark.asyncio
    async def test_registered_handler_receives_typed_event(self) -> None:
        bus = EventBus()
        handler = AsyncMock()
        event = light_event()

        bus.on(ResourceType.LIGHT, handler)
        await bus.dispatch(event)

        handler.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_only_matching_resource_type_is_dispatched(self) -> None:
        bus = EventBus()
        light_handler = AsyncMock()
        scene_handler = AsyncMock()
        bus.on(ResourceType.LIGHT, light_handler)
        bus.on(ResourceType.SCENE, scene_handler)

        await bus.dispatch(light_event())

        light_handler.assert_awaited_once()
        scene_handler.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_wildcard_receives_event(self) -> None:
        bus = EventBus()
        handler = AsyncMock()
        bus.on("*", handler)
        event = SceneEvent(id=uuid4(), type=ResourceType.SCENE)

        await bus.dispatch(event)

        handler.assert_awaited_once_with(event)


class TestUnsubscribe:
    @pytest.mark.asyncio
    async def test_unsubscribed_handler_is_not_called(self) -> None:
        bus = EventBus()
        handler = AsyncMock()
        bus.on(ResourceType.LIGHT, handler)
        bus.off(ResourceType.LIGHT, handler)

        await bus.dispatch(light_event())

        handler.assert_not_awaited()

    def test_unknown_subscription_does_not_raise(self) -> None:
        EventBus().off(ResourceType.LIGHT, AsyncMock())


class TestDispatch:
    @pytest.mark.asyncio
    async def test_returns_same_model(self) -> None:
        event = light_event()

        result = await EventBus().dispatch(event)

        assert result is event

    @pytest.mark.asyncio
    async def test_one_failing_handler_does_not_block_another(self) -> None:
        bus = EventBus()
        failing = AsyncMock(side_effect=RuntimeError("boom"))
        succeeding = AsyncMock()
        bus.on(ResourceType.LIGHT, failing)
        bus.on(ResourceType.LIGHT, succeeding)
        event = light_event()

        await bus.dispatch(event)

        succeeding.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_handlers_run_concurrently(self) -> None:
        bus = EventBus()
        call_order: list[str] = []

        async def slow_handler(event: LightEvent) -> None:
            await asyncio.sleep(0.05)
            call_order.append("slow")

        async def fast_handler(event: LightEvent) -> None:
            call_order.append("fast")

        bus.on(ResourceType.LIGHT, slow_handler)
        bus.on(ResourceType.LIGHT, fast_handler)
        await bus.dispatch(light_event())

        assert call_order == ["fast", "slow"]
