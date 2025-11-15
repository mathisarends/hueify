from collections.abc import Callable

from hueify.sse.models import (
    ButtonEvent,
    GroupedLightEvent,
    LightEvent,
    MotionEvent,
)
from hueify.sse.stream import EventStream
from hueify.sse.subscriber import EventSubscriber


class EventMonitor(EventSubscriber):
    def __init__(self) -> None:
        super().__init__()
        self._stream = EventStream()
        self._stream.subscribe(self.handle_event)

    async def start(self) -> None:
        self.logger.info("Starting event monitor")
        await self._stream.connect()

    def stop(self) -> None:
        self.logger.info("Stopping event monitor")
        self._stream.disconnect()

    def on_light_update(self, handler: Callable[[LightEvent], None]) -> None:
        self.on_light_event(handler)

    def on_button_press(self, handler: Callable[[ButtonEvent], None]) -> None:
        self.on_button_event(handler)

    def on_motion_detected(self, handler: Callable[[MotionEvent], None]) -> None:
        self.on_motion_event(handler)

    def on_grouped_light_update(
        self, handler: Callable[[GroupedLightEvent], None]
    ) -> None:
        self.on_grouped_light_event(handler)
