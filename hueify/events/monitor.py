import asyncio
from collections.abc import Callable

# hueify/events/monitor.py
from hueify.events.models import EventData, ResourceData, ResourceType
from hueify.events.stream import EventStream
from hueify.utils.logging import LoggingMixin


class EventMonitor(LoggingMixin):
    def __init__(self):
        self._stream = EventStream()
        self._stream.register_event_handler(self._route_event_to_handlers)

        self._light_handlers: list[Callable[[ResourceData], None]] = []
        self._button_handlers: list[Callable[[ResourceData], None]] = []
        self._motion_handlers: list[Callable[[ResourceData], None]] = []
        self._grouped_light_handlers: list[Callable[[ResourceData], None]] = []

    async def start(self) -> None:
        self.logger.info("Starting event monitor")
        await self._stream.connect()

    def stop(self) -> None:
        self.logger.info("Stopping event monitor")
        self._stream.disconnect()

    def on_light_update(self, handler: Callable[[ResourceData], None]) -> None:
        self._light_handlers.append(handler)

    def on_button_event(self, handler: Callable[[ResourceData], None]) -> None:
        self._button_handlers.append(handler)

    def on_motion_detected(self, handler: Callable[[ResourceData], None]) -> None:
        self._motion_handlers.append(handler)

    def on_grouped_light_update(self, handler: Callable[[ResourceData], None]) -> None:
        self._grouped_light_handlers.append(handler)

    async def _route_event_to_handlers(self, event_data: EventData) -> None:
        for resource_data in event_data.data:
            handlers = self._get_handlers_for_resource_type(resource_data.type)

            for handler in handlers:
                await self._invoke_handler(handler, resource_data)

    def _get_handlers_for_resource_type(self, resource_type: str) -> list[Callable]:
        handler_map = {
            ResourceType.LIGHT: self._light_handlers,
            ResourceType.BUTTON: self._button_handlers,
            ResourceType.MOTION: self._motion_handlers,
            ResourceType.GROUPED_LIGHT: self._grouped_light_handlers,
        }
        return handler_map.get(resource_type, [])

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
