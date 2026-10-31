import asyncio
import logging

from hueify.models import HueEvent
from hueify.sse.bus import EventBus

logger = logging.getLogger(__name__)

DEFAULT_EVENT_QUEUE_SIZE = 256


class EventQueue:
    """Deliver events in order, applying backpressure at a fixed capacity."""

    def __init__(self, bus: EventBus, capacity: int = DEFAULT_EVENT_QUEUE_SIZE) -> None:
        if isinstance(capacity, bool) or not isinstance(capacity, int) or capacity < 1:
            raise ValueError("The event queue size must be a positive integer")
        self._bus = bus
        self._queue: asyncio.Queue[HueEvent] = asyncio.Queue(maxsize=capacity)

    @property
    def pending(self) -> int:
        return self._queue.qsize()

    async def dispatch(self, event: HueEvent) -> HueEvent:
        if self._queue.full():
            logger.warning(
                "SSE event queue is full (%d); waiting for handlers",
                self._queue.maxsize,
            )
        await self._queue.put(event)
        return event

    async def run(self) -> None:
        while True:
            event = await self._queue.get()
            try:
                await self._bus.dispatch(event)
            except Exception:
                logger.exception("Error processing queued event")
            finally:
                self._queue.task_done()

    async def join(self) -> None:
        """Wait until queued events and their active handlers have finished."""
        await self._queue.join()

    def clear(self) -> None:
        while not self._queue.empty():
            self._queue.get_nowait()
            self._queue.task_done()
