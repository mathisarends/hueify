import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import cast, overload

from hueify.models import HueEvent, ResourceType
from hueify.sse.callbacks import CallbackContext

type EventResourceType = ResourceType | str
type EventHandler[T: HueEvent] = Callable[[T], Awaitable[None]]

logger = logging.getLogger(__name__)


class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler[HueEvent]]] = {}
        self._callbacks = CallbackContext()

    @property
    def in_handler(self) -> bool:
        return self._callbacks.active

    @overload
    def on[T: HueEvent](
        self, resource_type: EventResourceType, handler: EventHandler[T]
    ) -> EventHandler[T]: ...

    @overload
    def on[T: HueEvent](
        self, resource_type: EventResourceType, handler: None = None
    ) -> Callable[[EventHandler[T]], EventHandler[T]]: ...

    def on[T: HueEvent](
        self,
        resource_type: EventResourceType,
        handler: EventHandler[T] | None = None,
    ) -> EventHandler[T] | Callable[[EventHandler[T]], EventHandler[T]]:
        if handler is None:

            def decorator(callback: EventHandler[T]) -> EventHandler[T]:
                return self.on(resource_type, callback)

            return decorator

        key = str(resource_type)
        handlers = self._handlers.setdefault(key, [])
        handlers.append(cast(EventHandler[HueEvent], handler))
        return handler

    def off[T: HueEvent](
        self, resource_type: EventResourceType, handler: EventHandler[T]
    ) -> None:
        handlers = self._handlers.get(str(resource_type), [])
        typed_handler = cast(EventHandler[HueEvent], handler)
        if typed_handler in handlers:
            handlers.remove(typed_handler)

    async def dispatch[T: HueEvent](self, event: T) -> T:
        handlers = [
            *self._handlers.get(str(event.type), []),
            *self._handlers.get("*", []),
        ]
        with self._callbacks.enter():
            results = await asyncio.gather(
                *(handler(event) for handler in handlers),
                return_exceptions=True,
            )
        for result in results:
            if isinstance(result, Exception):
                logger.error("Handler failed for %s: %s", event.type, result)
        return event
