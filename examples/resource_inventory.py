"""Discover all bridge resources and resolve their owner references."""

import asyncio

from hueify import Hueify


async def main() -> None:
    async with Hueify() as hue:
        response = await hue.resources.list()
        for resource in response.data:
            print(resource.type, resource.id, getattr(resource, "name", None))
        for error in response.errors:
            print("bridge error:", error.description)

        lights = (await hue.lights.list()).data
        if lights:
            device = await hue.resources.get_one(lights[0].owner)
            print("first light belongs to:", device.model_dump(mode="json"))


if __name__ == "__main__":
    asyncio.run(main())
