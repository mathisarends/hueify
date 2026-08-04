import asyncio
import contextlib
from collections.abc import Callable
from typing import overload

from hueify.credentials import HueBridgeCredentials
from hueify.models import HueEvent
from hueify.sse.bus import EventBus, EventHandler, EventResourceType
from hueify.sse.stream import ServerSentEventStream


class EventStream:
    """Explicitly connected stream that emits typed Hue event models."""

    def __init__(self, credentials: HueBridgeCredentials) -> None:
        self._bus = EventBus()
        self._stream = ServerSentEventStream(credentials, self._bus)
        self._task: asyncio.Task[None] | None = None

    @property
    def connected(self) -> bool:
        return self._task is not None and not self._task.done()

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
        return self._bus.on(resource_type, handler)

    def off[T: HueEvent](
        self, resource_type: EventResourceType, handler: EventHandler[T]
    ) -> None:
        self._bus.off(resource_type, handler)

    async def connect(self) -> None:
        """Start listening in the background; calling twice is harmless."""
        if self.connected:
            return
        self._task = asyncio.create_task(self._stream.connect())
        await asyncio.sleep(0)

    async def close(self) -> None:
        self._stream.disconnect()
        if self._task is None:
            return
        if not self._task.done():
            self._task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await self._task
        self._task = None
