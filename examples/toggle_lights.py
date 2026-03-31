import asyncio
import logging

from hueify import Hueify

logging.basicConfig(level=logging.DEBUG)


async def main() -> None:
    async with Hueify() as hue:
        light_strip = hue.lights.from_name("Schreibtisch-Licht")
        print(f"Light strip: {light_strip}")

        await light_strip.turn_off()
        await light_strip.turn_on()
        await light_strip.set_brightness(50)

        await asyncio.sleep(5)

        room = hue.rooms.from_name("Mein Zimmer")
        await room.turn_off()
        await room.activate_scene("Nordlichter")

        await asyncio.sleep(5)

        print("light strip brightness:", light_strip.brightness_percentage)


if __name__ == "__main__":
    asyncio.run(main())
