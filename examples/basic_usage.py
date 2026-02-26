import asyncio

from hueify import Hueify, configure_logging


async def main() -> None:
    configure_logging("INFO")

    async with Hueify() as hue:
        print("Lights:", hue.lights.names)
        print("Rooms:", hue.rooms.names)
        print("Zones:", hue.zones.names)

        light_strip = hue.lights.from_name("Hue lightstrip plus 1")
        print(f"Light strip: {light_strip}")

        await light_strip.turn_on()
        await light_strip.set_brightness(50)

        await asyncio.sleep(10)

        print("light strip brightness:", light_strip.brightness_percentage)


if __name__ == "__main__":
    asyncio.run(main())
