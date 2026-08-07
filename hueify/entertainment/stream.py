"""Fixed-rate delivery of frames to one entertainment area.

The bridge stops listening to an area that falls silent for a few seconds, and
it forwards whatever arrived last to the lamps at about 25 Hz. Both point at
the same design: one loop that sends on a fixed clock, and colors that are
written into the next frame rather than sent themselves.

That decoupling is the whole job. A source produces colors whenever it happens
to have them - on a beat, on a packet, on a screen refresh - and the loop turns
that into an even stream of datagrams, drops nothing, queues nothing, and
resends the last frame when nothing new arrived, which is also what keeps the
area alive.
"""

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
"""Frames per second. The bridge accepts 50 and passes on about 25."""

MIN_RATE = 1
MAX_RATE = 60


@dataclass(frozen=True, slots=True)
class StreamStats:
    """What the sender loop has done so far."""

    frames_sent: int
    late_frames: int
    """Frames whose deadline had already passed - the loop skipped ahead."""

    started_at: datetime | None
    rate: int


class EntertainmentStream:
    """An open streaming session, sending frames until it is closed.

    Enter it to take the area over, and leave it to give the area back::

        async with hue.entertainment.stream(area) as stream:
            stream.set_all("#ff8800")
            await asyncio.sleep(5)

    Colors are written synchronously and read by the sender loop between
    awaits, so a frame is never sent half-updated - however many channels one
    write touches.
    """

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
        """The area being streamed to.

        Raises:
            EntertainmentError: If the stream is not open yet.
        """
        if self._area is None:
            raise EntertainmentError("The stream is not open")
        return self._area

    @property
    def channels(self) -> tuple[EntertainmentChannel, ...]:
        """The channels of the area, with the positions they sit at."""
        return tuple(self.area.channels)

    @property
    def frame(self) -> Frame:
        """The frame the next datagram will carry.

        Raises:
            EntertainmentError: If the stream is not open yet.
        """
        if self._frame is None:
            raise EntertainmentError("The stream is not open")
        return self._frame

    @property
    def rate(self) -> int:
        return self._rate

    @property
    def sending(self) -> bool:
        """Whether the sender loop is running."""
        return self._sender is not None and not self._sender.done()

    @property
    def error(self) -> Exception | None:
        """Why the stream stopped sending, if it stopped on its own.

        Outlives the session, so it is still readable after closing - which is
        where a caller that only noticed the lights going still looks.
        """
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
        """Set one channel of the next frame."""
        self.frame.set(channel_id, color, brightness)

    def set_all(self, color: Color, brightness: float = 1.0) -> None:
        """Set every channel of the next frame."""
        self.frame.set_all(color, brightness)

    async def open(self) -> Self:
        """Take the area over and start sending.

        Returns once frames are going out, which is what a caller that then
        goes off to produce colors wants. Calling it twice is harmless.

        Raises:
            EntertainmentAuthenticationError: If the bridge rejects the key.
            EntertainmentError: If the bridge does not take the connection.
            MissingDependencyError: If the entertainment extra is not installed.
        """
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
        """Stop sending, close the connection and give the area back."""
        if self._sender is not None:
            self._sender.cancel()
            # A sender that already failed has reported itself through `error`
            # and `wait_closed`; closing is not the place to hear it again.
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await self._sender
            self._sender = None

        if self._connection is not None:
            self._connection.close()
            self._connection = None

        await self._release_area()
        self._frame = None

    async def run(self, source: Renderer) -> None:
        """Let ``source`` paint every frame, until the stream stops.

        Returns when the stream is closed from elsewhere, and raises what
        stopped it otherwise - including anything the source raised, because a
        source that cannot paint has nothing left to send.
        """
        self._render = as_renderer(source)
        try:
            await self.wait_closed()
        finally:
            self._render = None

    async def wait_closed(self) -> None:
        """Wait for the sender loop to stop, and raise why if it failed."""
        sender = self._sender
        if sender is None:
            return
        try:
            await asyncio.shield(sender)
        except asyncio.CancelledError:
            if not sender.cancelled():
                raise  # the caller was cancelled, not the stream

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
        """Run the sender loop, keeping hold of whatever ends it."""
        try:
            await self._send_frames_forever()
        except asyncio.CancelledError:
            raise
        except Exception as error:
            self._error = error
            logger.warning("The entertainment stream stopped sending: %s", error)
            raise

    async def _send_frames_forever(self) -> None:
        """Send one datagram per tick, on a clock that does not drift.

        Deadlines are absolute, so the small cost of painting and encoding a
        frame does not accumulate into a slower and slower stream. A deadline
        that has already passed is not made up for either: the frame it wanted
        is stale, and catching up would only send a burst.
        """
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

    async def _release_area(self) -> None:
        """Hand the area back, tolerating a bridge that already took it away."""
        if self._area is None:
            return
        try:
            await self._areas.stop(self._area.id)
        except Exception as error:
            logger.debug("Could not stop streaming on the area: %s", error)


def _dtls_connection() -> "type[DtlsPskConnection]":
    """The DTLS client, imported only once streaming actually starts.

    Everything up to here works without the extra installed, which keeps
    listing and inspecting entertainment areas part of plain hueify.

    Raises:
        MissingDependencyError: If the entertainment extra is not installed.
    """
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
