import asyncio
import contextlib

from hueify.credentials import HueBridgeCredentials
from hueify.sse.bus import EventBus, EventHandler
from hueify.sse.stream import ServerSentEventStream


class EventStream:
    """Explicitly connected stream that emits the bridge's original JSON."""

    def __init__(self, credentials: HueBridgeCredentials) -> None:
        self._bus = EventBus()
        self._stream = ServerSentEventStream(credentials, self._bus)
        self._task: asyncio.Task[None] | None = None

    @property
    def connected(self) -> bool:
        return self._task is not None and not self._task.done()

    def subscribe(self, resource_type: str, handler: EventHandler) -> EventHandler:
        return self._bus.subscribe(resource_type, handler)

    def unsubscribe(self, resource_type: str, handler: EventHandler) -> None:
        self._bus.unsubscribe(resource_type, handler)

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
