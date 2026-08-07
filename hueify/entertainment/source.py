"""The seam an external package plugs a light show into.

Hueify owns the delivery: the connection, the frame rate, the datagrams. What
paints the frames it does not own, and does not need to know about - an audio
analyser, a screen grabber, a Spotify integration and a test all look the same
from here.

A source can push or be pulled, whichever suits it:

* Push - call ``stream.set_all(...)`` whenever a beat, a scene change or a
  packet arrives. The stream keeps sending at its own rate in between, so a
  source that falls quiet holds its last frame instead of dropping the
  connection.
* Pull - implement :class:`FrameSource` and hand it to ``stream.run(source)``.
  Then every frame is yours, on the clock, which is what a continuous effect
  wants.

Sources that own connections, audio devices or credentials should be async
context managers themselves; the stream does not manage their lifetime::

    async with SpotifySource(...) as source, hue.entertainment.stream(area) as stream:
        await stream.run(source)
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from hueify.entertainment.protocol import Frame


@dataclass(frozen=True, slots=True)
class Tick:
    """When the frame being painted is due, in monotonic seconds."""

    index: int
    """How many frames the stream has sent before this one."""

    elapsed: float
    """Seconds since the stream opened, which is the clock effects run on."""

    delta: float
    """Seconds since the previous frame - the nominal rate, unless it slipped."""


@runtime_checkable
class FrameSource(Protocol):
    """Something that paints one frame at a time."""

    def render(self, frame: Frame, tick: Tick) -> None:
        """Paint the frame that is about to be sent.

        Runs on the deadline of that frame, so it must not block or await:
        anything slow here delays the datagram. Read from state a background
        task of your own keeps up to date instead.
        """


type Renderer = FrameSource | Callable[[Frame, Tick], None]
"""A frame source, or the bare function of one."""


def as_renderer(source: Renderer) -> Callable[[Frame, Tick], None]:
    """The callable to invoke per frame, whichever shape the source has."""
    if isinstance(source, FrameSource):
        return source.render
    return source
