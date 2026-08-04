"""Getting from a name or an ID to a resource, and what happens when it is gone."""

import asyncio

from hueify import Hueify, ResourceNotFoundError

# adjust to a light name that exists in your setup
LIGHT_NAME = "Desk"


async def main() -> None:
    async with Hueify() as hue:
        # list() returns the raw Hue envelope with errors and data
        response = await hue.lights.list()
        print("lights:", [light.metadata.name for light in response.data])
        print("errors:", response.errors)

        # find_by_name() resolves the name shown in the Hue app
        light = await hue.lights.find_by_name(LIGHT_NAME)
        print(f"{light.metadata.name} has ID {light.id}")

        # get_one() takes an ID and hands back the resource itself
        same_light = await hue.lights.get_one(light.id)
        print("on:", same_light.on.on)

        # get() keeps the envelope if you want the errors alongside the data
        envelope = await hue.lights.get(light.id)
        print("payload:", envelope.model_dump(mode="json"))

        # rooms, zones and scenes are looked up the same way
        for namespace in (hue.rooms, hue.zones, hue.scenes):
            names = [item.metadata.name for item in (await namespace.list()).data]
            print(f"{namespace.resource_type}: {names}")

        # a name that does not exist tells you which ones do
        try:
            await hue.lights.find_by_name("Does not exist")
        except ResourceNotFoundError as error:
            print("expected:", error)


if __name__ == "__main__":
    asyncio.run(main())
