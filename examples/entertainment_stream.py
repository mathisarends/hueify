"""Stream colors to an entertainment area over UDP.

Needs the optional extra and a client key:

    pip install "hueify[entertainment]"
    hueify setup            # prints HUE_CLIENT_KEY as well
"""

import asyncio
import colorsys
import contextlib
import math

from hueify import Hueify
from hueify.entertainment import Frame, Tick

AREA_NAME = "Musikbereich"  # an entertainment area from your Hue app


class Wave:
    """A hue that travels through the room from left to right.

    A source paints one frame at a time and nothing else - where the colors
    come from is its own business, be it an audio analysis, a screen grabber or
    trigonometry.
    """

    def __init__(self, positions: dict[int, float], speed: float = 0.3) -> None:
        self._positions = positions
        self._speed = speed

    def render(self, frame: Frame, tick: Tick) -> None:
        for channel_id, x in self._positions.items():
            hue = (tick.elapsed * self._speed + (x + 1) / 4) % 1
            red, green, blue = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
            frame.set(
                channel_id, (round(red * 255), round(green * 255), round(blue * 255))
            )


async def main() -> None:
    async with Hueify() as hue:
        area = await hue.entertainment.find_by_name(AREA_NAME)
        if area.is_streaming:
            print(f"{AREA_NAME} is already being streamed to by another application.")
            return

        async with hue.entertainment.stream(area) as stream:
            print(f"Streaming to {AREA_NAME}, {len(stream.channels)} channels.")

            # Push: set colors whenever you have them, the stream keeps sending
            # at its own rate in between.
            for color in ("#ff0000", "#00ff00", "#0000ff"):
                stream.set_all(color)
                await asyncio.sleep(1)

            # Or dim the whole area on a curve, one write per step.
            for step in range(50):
                stream.set_all("#ffaa00", brightness=abs(math.cos(step / 8)))
                await asyncio.sleep(0.04)

            # Pull: hand over every frame to a source until it is done.
            positions = {
                channel.channel_id: channel.position.x for channel in stream.channels
            }
            with contextlib.suppress(TimeoutError):
                async with asyncio.timeout(10):
                    await stream.run(Wave(positions))

        print(f"Sent {stream.stats.frames_sent} frames at {stream.rate} fps.")


if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(main())
