import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Any

type JsonObject = dict[str, Any]
type EventHandler = Callable[[JsonObject], Awaitable[None]]

logger = logging.getLogger(__name__)


class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler]] = {}

    def subscribe(self, resource_type: str, handler: EventHandler) -> EventHandler:
        """Subscribe to a Hue resource type, or ``*`` for every event."""
        self._handlers.setdefault(resource_type, []).append(handler)
        return handler

    def unsubscribe(self, resource_type: str, handler: EventHandler) -> None:
        handlers = self._handlers.get(resource_type, [])
        if handler in handlers:
            handlers.remove(handler)

    async def dispatch(self, event: JsonObject) -> JsonObject:
        resource_type = event.get("type")
        if not isinstance(resource_type, str):
            logger.warning("Ignoring Hue event without a string 'type': %r", event)
            return event

        handlers = [
            *self._handlers.get(resource_type, []),
            *self._handlers.get("*", []),
        ]
        results = await asyncio.gather(
            *(handler(event) for handler in handlers),
            return_exceptions=True,
        )
        for result in results:
            if isinstance(result, Exception):
                logger.error("Handler failed for %s: %s", resource_type, result)
        return event
