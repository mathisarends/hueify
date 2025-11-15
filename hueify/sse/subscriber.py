from abc import ABC
from collections.abc import Callable
from typing import TypeVar

from hueify.sse.models import (
    ButtonEvent,
    EventData,
    GroupedLightEvent,
    HueEvent,
    LightEvent,
    MotionEvent,
    UnknownEvent,
)
from hueify.utils.logging import LoggingMixin

T = TypeVar("T", bound=HueEvent)


class EventSubscriber(LoggingMixin, ABC):
    def __init__(self) -> None:
        self._handlers: dict[type[HueEvent], list[Callable]] = {}

    async def handle_event(self, event_data: EventData) -> None:
        for hue_event in event_data.data:
            await self._dispatch_event(hue_event)

    async def _dispatch_event(self, hue_event: HueEvent | UnknownEvent) -> None:
        if isinstance(hue_event, UnknownEvent):
            self.logger.debug(f"Skipping unknown event type: {hue_event.type}")
            return

        event_type = type(hue_event)
        handlers = self._handlers.get(event_type, [])

        for handler in handlers:
            try:
                handler(hue_event)
            except Exception as e:
                self.logger.error(
                    f"Error in handler for {event_type.__name__}: {e}", exc_info=True
                )

    def on_button_event(self, handler: Callable[[ButtonEvent], None]) -> None:
        self._register_handler(ButtonEvent, handler)

    def on_light_event(self, handler: Callable[[LightEvent], None]) -> None:
        self._register_handler(LightEvent, handler)

    def on_motion_event(self, handler: Callable[[MotionEvent], None]) -> None:
        self._register_handler(MotionEvent, handler)

    def on_grouped_light_event(
        self, handler: Callable[[GroupedLightEvent], None]
    ) -> None:
        self._register_handler(GroupedLightEvent, handler)

    def _register_handler(
        self, event_type: type[T], handler: Callable[[T], None]
    ) -> None:
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
