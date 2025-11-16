import asyncio
from collections.abc import Callable
from typing import TypeVar
from uuid import UUID

from hueify.sse.models import (
    ButtonEvent,
    EventData,
    EventType,
    GroupedLightEvent,
    HueEvent,
    LightEvent,
    MotionEvent,
    RelativeRotaryEvent,
    SceneEvent,
    UnknownEvent,
)
from hueify.sse.stream import get_event_stream
from hueify.utils.logging import LoggingMixin

T = TypeVar("T", bound=HueEvent)


class EventBus(LoggingMixin):
    def __init__(self) -> None:
        self._stream = get_event_stream()
        self._handlers: dict[type[HueEvent], list[Callable[[HueEvent], None]]] = {}
        self._connection_task: asyncio.Task | None = None

    async def _ensure_connected(self) -> None:
        if self._connection_task is None or self._connection_task.done():
            self._stream.subscribe(self._dispatch_event)
            self._connection_task = asyncio.create_task(self._stream.connect())
            self.logger.info("Event stream connection started")

    def subscribe_to_light(
        self,
        handler: Callable[[LightEvent], None],
        light_id: UUID | None = None,
        event_type: EventType | None = None,
    ) -> None:
        self._subscribe_typed(
            LightEvent,
            handler,
            resource_id=light_id,
            event_type=event_type,
        )

    def subscribe_to_button(
        self,
        handler: Callable[[ButtonEvent], None],
        button_id: UUID | None = None,
    ) -> None:
        self._subscribe_typed(ButtonEvent, handler, resource_id=button_id)

    def subscribe_to_motion(
        self,
        handler: Callable[[MotionEvent], None],
        motion_sensor_id: UUID | None = None,
    ) -> None:
        self._subscribe_typed(MotionEvent, handler, resource_id=motion_sensor_id)

    def subscribe_to_grouped_light(
        self,
        handler: Callable[[GroupedLightEvent], None],
        group_id: UUID | None = None,
    ) -> None:
        self._subscribe_typed(GroupedLightEvent, handler, resource_id=group_id)

    def subscribe_to_scene(
        self,
        handler: Callable[[SceneEvent], None],
        scene_id: UUID | None = None,
    ) -> None:
        self._subscribe_typed(SceneEvent, handler, resource_id=scene_id)

    def subscribe_to_rotary(
        self,
        handler: Callable[[RelativeRotaryEvent], None],
        rotary_id: UUID | None = None,
    ) -> None:
        self._subscribe_typed(RelativeRotaryEvent, handler, resource_id=rotary_id)

    def _subscribe_typed(
        self,
        event_class: type[T],
        handler: Callable[[T], None],
        resource_id: UUID | None = None,
        event_type: EventType | None = None,
    ) -> None:
        async def filtered_handler(event_data: EventData) -> None:
            if event_type is not None and event_data.type != event_type:
                return

            for hue_event in event_data.data:
                if isinstance(hue_event, UnknownEvent):
                    continue

                if not isinstance(hue_event, event_class):
                    continue

                if resource_id is not None and hue_event.id != resource_id:
                    continue

                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(hue_event)
                    else:
                        handler(hue_event)
                except Exception as e:
                    self.logger.error(
                        f"Error in handler for {event_class.__name__}: {e}",
                        exc_info=True,
                    )

        if event_class not in self._handlers:
            self._handlers[event_class] = []

        self._handlers[event_class].append(filtered_handler)

    async def _dispatch_event(self, event_data: EventData) -> None:
        for handlers in self._handlers.values():
            for handler in handlers:
                await handler(event_data)

    def stop(self) -> None:
        self._stream.disconnect()
        if self._connection_task and not self._connection_task.done():
            self._connection_task.cancel()
        self.logger.info("Event stream stopped")


_event_bus: EventBus | None = None
_event_bus_lock = asyncio.Lock()


async def get_event_bus() -> EventBus:
    global _event_bus

    async with _event_bus_lock:
        if _event_bus is None:
            _event_bus = EventBus()
            await _event_bus._ensure_connected()

        return _event_bus
