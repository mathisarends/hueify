"""A light switch: flip whatever state the light is in right now."""

import asyncio

from hueify import Hueify

# adjust to a light name that exists in your setup
LIGHT_NAME = "Desk"


async def main() -> None:
    async with Hueify() as hue:
        light = await hue.lights.find(LIGHT_NAME)

        print("on:", await hue.lights.is_on(light.id))

        await hue.lights.toggle(light.id)
        await asyncio.sleep(2)
        print("on:", await hue.lights.is_on(light.id))

        await hue.lights.toggle(light.id, transition=2)
        await asyncio.sleep(3)
        print("on:", await hue.lights.is_on(light.id))


if __name__ == "__main__":
    asyncio.run(main())
