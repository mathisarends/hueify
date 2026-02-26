"""
Demonstrates that Light and GroupedLights instances are live views on the cache.

Once a Light or GroupedLights object is created via from_name(), its properties
(brightness_percentage, is_on, etc.) always reflect the current state from the
in-memory cache, which is kept up-to-date via SSE events from the Hue Bridge.
No need to re-fetch or re-create the object to get fresh values.
"""

import asyncio

from hueify import Hueify, configure_logging


async def main() -> None:
    configure_logging("INFO")

    async with Hueify() as hue:
        light = hue.lights.from_name("Desk lamp")
        room = hue.rooms.from_name("Living room")

        print(f"[before] light brightness: {light.brightness_percentage}%")
        print(f"[before] room brightness:  {room.brightness_percentage}%")

        await hue.lights.set_brightness("Desk lamp", 20)
        await hue.rooms.set_brightness("Living room", 80)

        await asyncio.sleep(1)

        print(f"[after]  light brightness: {light.brightness_percentage}%")
        print(f"[after]  room brightness:  {room.brightness_percentage}%")


if __name__ == "__main__":
    asyncio.run(main())
