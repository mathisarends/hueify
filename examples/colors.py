"""The color formats a command accepts, and how they map to Hue values."""

import asyncio

from hueify import Hueify
from hueify.color import NAMED_COLORS, kelvin_to_mirek, to_xy, xy_to_hex
from hueify.models import ColorXY

# adjust to a light name that exists in your setup
LIGHT_NAME = "Desk"


async def main() -> None:
    print("named colors:", ", ".join(sorted(NAMED_COLORS)))
    print("#ff8800 ->", to_xy("#ff8800"))
    print("2700K ->", kelvin_to_mirek(2700), "mirek")

    async with Hueify() as hue:
        light = await hue.lights.find_by_name(LIGHT_NAME)

        for color in ("#ff8800", "f80", "red", "warm white", (0, 128, 255)):
            await hue.lights.set_color(light.id, color, brightness=70)
            print(f"{color!r} -> {to_xy(color)}")
            await asyncio.sleep(2)

        # CIE xy values from the Hue API can be passed through unchanged
        await hue.lights.set_color(light.id, ColorXY(x=0.5, y=0.4))
        await asyncio.sleep(2)

        # and read back the current color as something you can print
        current = await hue.lights.get_one(light.id)
        if current.color and current.color.xy:
            brightness = current.dimming.brightness if current.dimming else 100
            print("current color:", xy_to_hex(current.color.xy, brightness))

        await hue.lights.turn_off(light.id)


if __name__ == "__main__":
    asyncio.run(main())
