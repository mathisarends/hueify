from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from hueify.entertainment.protocol import Frame


@dataclass(frozen=True, slots=True)
class Tick:
    """Timing for a frame, measured with the monotonic clock."""

    index: int
    elapsed: float
    delta: float


@runtime_checkable
class FrameSource(Protocol):
    def render(self, frame: Frame, tick: Tick) -> None:
        """Paint the next frame without blocking."""


type Renderer = FrameSource | Callable[[Frame, Tick], None]


def as_renderer(source: Renderer) -> Callable[[Frame, Tick], None]:
    if isinstance(source, FrameSource):
        return source.render
    return source
