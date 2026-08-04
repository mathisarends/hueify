"""Every command a single light understands."""

import asyncio

from hueify import Hueify

# adjust to a light name that exists in your setup
LIGHT_NAME = "Desk"


async def main() -> None:
    async with Hueify() as hue:
        light = await hue.lights.find(LIGHT_NAME)
        lights = hue.lights

        await lights.turn_on(light.id)
        await asyncio.sleep(1)

        await lights.turn_off(light.id)
        await asyncio.sleep(1)

        # toggle reads the current state and flips it
        await lights.toggle(light.id)
        await asyncio.sleep(1)

        # absolute brightness in percent; 0 switches the light off
        await lights.set_brightness(light.id, 80)
        await asyncio.sleep(1)

        # relative steps, applied by the bridge without reading first
        await lights.dim(light.id, by=30)
        await asyncio.sleep(1)
        await lights.brighten(light.id)
        await asyncio.sleep(1)

        # warm white in kelvin, the bridge works in mirek
        await lights.set_color_temperature(light.id, 2200, brightness=60)
        await asyncio.sleep(1)

        await lights.set_color(light.id, "#8800ff")
        await asyncio.sleep(1)

        # set_state sends exactly what you pass and nothing else
        await lights.set_state(light.id, on=True, brightness=45, kelvin=4000)
        await asyncio.sleep(1)

        # make the lamp breathe so you can tell which one it is
        await lights.identify(light.id)
        await asyncio.sleep(2)

        print("still on:", await lights.is_on(light.id))
        await lights.turn_off(light.id, transition=2)


if __name__ == "__main__":
    asyncio.run(main())
