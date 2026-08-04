"""The two ways to set a color, and how they map to Hue values."""

import asyncio

from hueify import Hueify
from hueify.color import kelvin_to_mirek, to_xy, xy_to_hex

# adjust to a light name that exists in your setup
LIGHT_NAME = "Desk"


async def main() -> None:
    print("#ff8800 ->", to_xy("#ff8800"))
    print("2700K ->", kelvin_to_mirek(2700), "mirek")

    async with Hueify() as hue:
        light = await hue.lights.find_by_name(LIGHT_NAME)

        await hue.lights.set_hex(light.id, "#ff8800", brightness=70)
        await asyncio.sleep(2)

        await hue.lights.set_rgb(light.id, 0, 128, 255, brightness=70)
        await asyncio.sleep(2)

        # to_xy also resolves named colors, for values that arrive as strings
        await hue.lights.set_state(light.id, on=True, color=to_xy("warm white"))
        await asyncio.sleep(2)

        # and read back the current color as something you can print
        current = await hue.lights.get_one(light.id)
        if current.xy:
            print("current color:", xy_to_hex(current.xy, current.brightness or 100))

        await hue.lights.turn_off(light.id)


if __name__ == "__main__":
    asyncio.run(main())
