import asyncio
import contextlib
import logging
import time
from collections.abc import Callable
from datetime import datetime
from typing import overload

import httpx

from hueify.credentials import HueBridgeCredentials
from hueify.errors import StreamAuthenticationError
from hueify.models import HueEvent
from hueify.sse.bus import EventBus, EventHandler, EventResourceType
from hueify.sse.connection import ConnectionHandler, ConnectionStatus, StreamConnection
from hueify.sse.retry import Backoff, ReconnectPolicy
from hueify.sse.stream import ServerSentEventStream

logger = logging.getLogger(__name__)


class EventStream:
    """Self-healing event stream that reconnects until it is stopped.

    Reconnecting cannot replay what the bridge sent while the connection was
    down, so a handler that keeps its own copy of the bridge state should
    re-read that state whenever the connection comes back.
    """

    def __init__(
        self,
        credentials: HueBridgeCredentials,
        policy: ReconnectPolicy | None = None,
    ) -> None:
        self._policy = policy or ReconnectPolicy()
        self._bus = EventBus()
        self._connection = StreamConnection()
        self._stream = ServerSentEventStream(
            credentials, self._bus, self._connection, self._policy
        )
        self._task: asyncio.Task[None] | None = None
        self._last_error: Exception | None = None
        self._connection.on_change(self._clear_error_after_recovery)

    @property
    def running(self) -> bool:
        """Whether the stream is being supervised, connected or reconnecting."""
        return self._task is not None and not self._task.done()

    @property
    def connected(self) -> bool:
        """Whether the connection to the bridge is open right now."""
        return self._connection.connected

    @property
    def status(self) -> ConnectionStatus:
        return self._connection.status

    @property
    def last_event_at(self) -> datetime | None:
        return self._connection.last_event_at

    @property
    def last_error(self) -> Exception | None:
        """The latest connection failure, or ``None`` after recovery."""
        return None if self.connected else self._last_error

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

    def on_connection_change(self, handler: ConnectionHandler) -> ConnectionHandler:
        """Register a handler for connection loss and recovery."""
        return self._connection.on_change(handler)

    def off_connection_change(self, handler: ConnectionHandler) -> None:
        self._connection.off_change(handler)

    async def start(self, timeout: float | None = None) -> None:
        """Start listening in the background; calling twice is harmless.

        Returns as soon as the stream is supervised. Pass a timeout to wait for
        the first connection instead and raise when it does not arrive; the
        stream keeps reconnecting either way.
        """
        if not self.running:
            self._task = asyncio.create_task(self._supervise())
            await asyncio.sleep(0)

        if timeout is None or await self.wait_connected(timeout):
            return
        if self._last_error is not None:
            raise self._last_error
        raise TimeoutError(f"The bridge did not answer within {timeout}s")

    async def wait_connected(self, timeout: float | None = None) -> bool:
        """Wait for the connection to be open, returning ``False`` on timeout."""
        return await self._connection.wait_connected(timeout)

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None
        await self._connection.closed()

    async def _supervise(self) -> None:
        try:
            await self._reconnect_forever()
        except StreamAuthenticationError as error:
            self._last_error = error
            logger.error("Event stream stopped: %s", error)
        except Exception as error:
            self._last_error = error
            logger.exception("Event stream supervisor stopped unexpectedly")

    async def _reconnect_forever(self) -> None:
        backoff = Backoff(self._policy)

        while True:
            started = time.monotonic()
            await self._run_connection()

            if time.monotonic() - started >= self._policy.healthy_after:
                backoff.reset()

            delay = backoff.next_delay()
            logger.info("Reconnecting to the event stream in %.1fs", delay)
            await asyncio.sleep(delay)

    async def _run_connection(self) -> None:
        """Run one connection to its end; only unrecoverable failures propagate."""
        try:
            await self._stream.run_once()
            logger.info("Event stream closed by the bridge")
        except httpx.ReadTimeout:
            # The bridge only speaks when something changes, so silence says
            # nothing about its health - reconnect quietly and carry on.
            logger.debug("No data for %.0fs, reconnecting", self._policy.read_timeout)
        except httpx.HTTPError as error:
            self._last_error = error
            logger.warning("Event stream connection lost: %s", error)
        finally:
            await self._connection.closed()

    async def _clear_error_after_recovery(self, status: ConnectionStatus) -> None:
        if status.connected:
            self._last_error = None
