import asyncio
import contextlib
import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from types import TracebackType
from typing import TYPE_CHECKING, Self

from hueify.color import Color
from hueify.credentials import HueBridgeCredentials
from hueify.entertainment.protocol import Frame
from hueify.entertainment.source import Renderer, Tick, as_renderer
from hueify.errors import (
    EntertainmentError,
    MissingCredentialsError,
    MissingDependencyError,
)
from hueify.models import EntertainmentChannel, EntertainmentConfiguration
from hueify.resources.base import ResourceId

if TYPE_CHECKING:
    from hueify.entertainment.dtls import DtlsPskConnection
    from hueify.entertainment.namespace import EntertainmentNamespace

logger = logging.getLogger(__name__)

DEFAULT_RATE = 50

MIN_RATE = 1
MAX_RATE = 60


@dataclass(frozen=True, slots=True)
class StreamStats:
    frames_sent: int
    late_frames: int
    started_at: datetime | None
    rate: int


class EntertainmentStream:
    """A fixed-rate streaming session for one entertainment area."""

    def __init__(
        self,
        area: EntertainmentConfiguration | ResourceId,
        areas: "EntertainmentNamespace",
        credentials: HueBridgeCredentials,
        rate: int = DEFAULT_RATE,
    ) -> None:
        if not MIN_RATE <= rate <= MAX_RATE:
            raise ValueError(
                f"A stream runs at {MIN_RATE} to {MAX_RATE} frames per second, "
                f"got {rate}"
            )
        if credentials.hue_client_key is None:
            raise MissingCredentialsError(_MISSING_CLIENT_KEY_MESSAGE)

        self._requested_area = area
        self._areas = areas
        self._credentials = credentials
        self._rate = rate

        self._area: EntertainmentConfiguration | None = None
        self._frame: Frame | None = None
        self._connection: DtlsPskConnection | None = None
        self._sender: asyncio.Task[None] | None = None
        self._render: Callable[[Frame, Tick], None] | None = None
        self._started_at: datetime | None = None
        self._error: Exception | None = None
        self._frames_sent = 0
        self._late_frames = 0

    @property
    def area(self) -> EntertainmentConfiguration:
        if self._area is None:
            raise EntertainmentError("The stream is not open")
        return self._area

    @property
    def channels(self) -> tuple[EntertainmentChannel, ...]:
        return tuple(self.area.channels)

    @property
    def frame(self) -> Frame:
        if self._frame is None:
            raise EntertainmentError("The stream is not open")
        return self._frame

    @property
    def rate(self) -> int:
        return self._rate

    @property
    def sending(self) -> bool:
        return self._sender is not None and not self._sender.done()

    @property
    def error(self) -> Exception | None:
        """The failure that stopped the sender, preserved after closing."""
        return self._error

    @property
    def stats(self) -> StreamStats:
        return StreamStats(
            frames_sent=self._frames_sent,
            late_frames=self._late_frames,
            started_at=self._started_at,
            rate=self._rate,
        )

    def set(self, channel_id: int, color: Color, brightness: float = 1.0) -> None:
        self.frame.set(channel_id, color, brightness)

    def set_all(self, color: Color, brightness: float = 1.0) -> None:
        self.frame.set_all(color, brightness)

    async def open(self) -> Self:
        """Take the area over and start sending; calling twice is harmless."""
        if self.sending:
            return self

        connection_type = _dtls_connection()
        self._area = await self._resolve_area()
        self._frame = Frame(channel.channel_id for channel in self._area.channels)

        await self._areas.start(self._area.id)
        try:
            self._connection = await connection_type.connect(
                self._credentials.hue_bridge_ip,
                self._credentials.hue_app_key,
                str(self._credentials.hue_client_key),
            )
        except BaseException:
            await self._release_area()
            raise

        self._started_at = datetime.now(UTC)
        self._sender = asyncio.create_task(self._send_frames())
        return self

    async def close(self) -> None:
        await self._stop_sender()

        if self._connection is not None:
            self._connection.close()
            self._connection = None

        await self._release_area()
        self._frame = None

    async def run(self, source: Renderer) -> None:
        """Let ``source`` paint frames until the stream stops."""
        self._render = as_renderer(source)
        try:
            await self.wait_closed()
        finally:
            self._render = None

    async def wait_closed(self) -> None:
        sender = self._sender
        if sender is None:
            return
        try:
            await asyncio.shield(sender)
        except asyncio.CancelledError:
            if sender.cancelled():
                return
            raise

    async def __aenter__(self) -> Self:
        return await self.open()

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.close()

    async def _send_frames(self) -> None:
        try:
            await self._send_frames_forever()
        except asyncio.CancelledError:
            raise
        except Exception as error:
            self._error = error
            logger.warning("The entertainment stream stopped sending: %s", error)
            raise

    async def _send_frames_forever(self) -> None:
        """Use absolute deadlines so rendering time does not accumulate."""
        assert self._connection is not None

        loop = asyncio.get_running_loop()
        interval = 1 / self._rate
        area_id = self.area.id
        frame = self.frame

        started = loop.time()
        previous = started
        deadline = started + interval
        sequence = 0

        while True:
            await asyncio.sleep(deadline - loop.time())
            now = loop.time()

            if self._render is not None:
                self._render(frame, Tick(sequence, now - started, now - previous))

            self._connection.send(frame.encode(area_id, sequence))
            self._frames_sent += 1
            sequence += 1
            previous = now

            deadline += interval
            if deadline <= now:
                self._late_frames += 1
                deadline = now + interval

    async def _resolve_area(self) -> EntertainmentConfiguration:
        if isinstance(self._requested_area, EntertainmentConfiguration):
            return self._requested_area
        return await self._areas.get_one(self._requested_area)

    async def _stop_sender(self) -> None:
        if self._sender is None:
            return
        self._sender.cancel()
        with contextlib.suppress(asyncio.CancelledError, Exception):
            await self._sender
        self._sender = None

    async def _release_area(self) -> None:
        if self._area is None:
            return
        try:
            await self._areas.stop(self._area.id)
        except Exception as error:
            logger.debug("Could not stop streaming on the area: %s", error)


def _dtls_connection() -> "type[DtlsPskConnection]":
    try:
        from hueify.entertainment.dtls import DtlsPskConnection
    except ImportError as error:
        raise MissingDependencyError(
            "Entertainment streaming needs the DTLS support of the optional "
            "entertainment extra: pip install 'hueify[entertainment]'"
        ) from error
    return DtlsPskConnection


_MISSING_CLIENT_KEY_MESSAGE = (
    "No Hue client key found, and entertainment streaming cannot work without "
    "one.\n"
    "The bridge only hands it out while registering an application, so run "
    "`hueify setup` again and set HUE_CLIENT_KEY from its output, or pass "
    "client_key to Hueify() directly."
)
