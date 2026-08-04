"""Fading changes over time instead of jumping to them.

Every command takes a transition: seconds as a number, or a timedelta.
The bridge runs the fade, so nothing has to be stepped from Python.
"""

import asyncio
from datetime import timedelta

from hueify import Hueify

# adjust to a light name that exists in your setup
LIGHT_NAME = "Desk"


async def main() -> None:
    async with Hueify() as hue:
        light = await hue.lights.find_by_name(LIGHT_NAME)

        # a slow sunrise: start deep warm and barely visible
        await hue.lights.turn_on(light.id, brightness=1, kelvin=2000)
        await asyncio.sleep(1)

        # then fade to bright daylight over ten seconds
        await hue.lights.set_state(
            light.id,
            brightness=100,
            kelvin=4000,
            transition=timedelta(seconds=10),
        )
        await asyncio.sleep(11)

        # seconds as a plain number work just as well
        await hue.lights.set_color(light.id, "#3355ff", transition=3)
        await asyncio.sleep(4)

        # a fade of 0 is the default: change immediately
        await hue.lights.set_brightness(light.id, 30)
        await asyncio.sleep(1)

        await hue.lights.turn_off(light.id, transition=timedelta(seconds=5))


if __name__ == "__main__":
    asyncio.run(main())
