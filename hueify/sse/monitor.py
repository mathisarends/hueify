import asyncio
from collections.abc import Callable

from hueify.sse.models import (
    ButtonResource,
    EventData,
    GroupedLightResource,
    LightResource,
    MotionResource,
    ResourceData,
)
from hueify.sse.stream import EventStream
from hueify.utils.logging import LoggingMixin


class EventMonitor(LoggingMixin):
    def __init__(self):
        self._stream = EventStream()
        self._stream.register_event_handler(self._route_event_to_handlers)

        self._light_handlers: list[Callable[[LightResource], None]] = []
        self._button_handlers: list[Callable[[ButtonResource], None]] = []
        self._motion_handlers: list[Callable[[MotionResource], None]] = []
        self._grouped_light_handlers: list[Callable[[GroupedLightResource], None]] = []

    async def start(self) -> None:
        self.logger.info("Starting event monitor")
        await self._stream.connect()

    def stop(self) -> None:
        self.logger.info("Stopping event monitor")
        self._stream.disconnect()

    def on_light_update(self, handler: Callable[[LightResource], None]) -> None:
        self._light_handlers.append(handler)

    def on_button_event(self, handler: Callable[[ButtonResource], None]) -> None:
        self._button_handlers.append(handler)

    def on_motion_detected(self, handler: Callable[[MotionResource], None]) -> None:
        self._motion_handlers.append(handler)

    def on_grouped_light_update(
        self, handler: Callable[[GroupedLightResource], None]
    ) -> None:
        self._grouped_light_handlers.append(handler)

    async def _route_event_to_handlers(self, event_data: EventData) -> None:
        for resource_data in event_data.data:
            if isinstance(resource_data, LightResource):
                await self._invoke_handlers(self._light_handlers, resource_data)
            elif isinstance(resource_data, ButtonResource):
                await self._invoke_handlers(self._button_handlers, resource_data)
            elif isinstance(resource_data, MotionResource):
                await self._invoke_handlers(self._motion_handlers, resource_data)
            elif isinstance(resource_data, GroupedLightResource):
                await self._invoke_handlers(self._grouped_light_handlers, resource_data)

    async def _invoke_handlers(
        self, handlers: list[Callable], resource_data: ResourceData
    ) -> None:
        for handler in handlers:
            await self._invoke_handler(handler, resource_data)

    async def _invoke_handler(
        self, handler: Callable[[ResourceData], None], resource_data: ResourceData
    ) -> None:
        try:
            if asyncio.iscoroutinefunction(handler):
                await handler(resource_data)
            else:
                handler(resource_data)
        except Exception as e:
            self.logger.error(f"Handler error: {e}", exc_info=True)
