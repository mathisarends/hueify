import asyncio
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ConnectionStatus:
    """Whether the bridge stream is open, since when, and when it last spoke."""

    connected: bool
    since: datetime
    last_event_at: datetime | None


type ConnectionHandler = Callable[[ConnectionStatus], Awaitable[None]]


class StreamConnection:
    """Live state of the SSE connection, shared by the stream and its supervisor."""

    def __init__(self) -> None:
        self._connected = False
        self._since = _now()
        self._last_event_at: datetime | None = None
        self._handlers: list[ConnectionHandler] = []
        self._is_open = asyncio.Event()

    @property
    def connected(self) -> bool:
        return self._connected

    @property
    def since(self) -> datetime:
        return self._since

    @property
    def last_event_at(self) -> datetime | None:
        return self._last_event_at

    @property
    def status(self) -> ConnectionStatus:
        return ConnectionStatus(
            connected=self._connected,
            since=self._since,
            last_event_at=self._last_event_at,
        )

    def on_change(self, handler: ConnectionHandler) -> ConnectionHandler:
        self._handlers.append(handler)
        return handler

    def off_change(self, handler: ConnectionHandler) -> None:
        if handler in self._handlers:
            self._handlers.remove(handler)

    def record_event(self) -> None:
        self._last_event_at = _now()

    async def wait_connected(self, timeout: float | None = None) -> bool:
        try:
            await asyncio.wait_for(self._is_open.wait(), timeout)
        except TimeoutError:
            return False
        return True

    async def opened(self) -> None:
        await self._transition(connected=True)

    async def closed(self) -> None:
        await self._transition(connected=False)

    async def _transition(self, *, connected: bool) -> None:
        if self._connected == connected:
            return

        self._connected = connected
        self._since = _now()
        if connected:
            self._is_open.set()
        else:
            self._is_open.clear()

        await self._notify()

    async def _notify(self) -> None:
        status = self.status
        results = await asyncio.gather(
            *(handler(status) for handler in self._handlers),
            return_exceptions=True,
        )
        for result in results:
            if isinstance(result, Exception):
                logger.error("Connection handler failed: %s", result)


def _now() -> datetime:
    return datetime.now(UTC)
