import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

EventHandler = Callable[[T], Awaitable[None]]

logger = logging.getLogger(__name__)


class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[type[BaseModel], list[EventHandler]] = {}

    def subscribe(self, event_type: type[T], handler: EventHandler[T]) -> None:
        self._handlers.setdefault(event_type, []).append(handler)
        logger.debug(f"Subscribed to {event_type.__name__}")

    def unsubscribe(self, event_type: type[T], handler: EventHandler[T]) -> None:
        if event_type in self._handlers and handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)

    async def dispatch(self, event: T) -> T:
        event_type = type(event)
        handlers = self._handlers.get(event_type, [])
        logger.debug(f"Dispatching {event_type.__name__} to {len(handlers)} handler(s)")

        if not handlers:
            logger.warning(f"No handlers registered for {event_type.__name__}")
            return event

        results = await asyncio.gather(
            *[handler(event) for handler in handlers],
            return_exceptions=True,
        )

        for result in results:
            if isinstance(result, Exception):
                logger.error(
                    f"Handler failed for {event_type.__name__}: {result}",
                    exc_info=result,
                )

        return event
