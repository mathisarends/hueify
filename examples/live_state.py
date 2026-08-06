"""
Demonstrates reacting to bridge changes in real time via the event stream.

Hueify is a stateless, JSON-first client: resources returned by list()/find()
are snapshots that go stale the moment something changes. To learn about updates
as they happen (including ones made by other apps or physical switches), subscribe
to the event stream instead of re-polling the REST endpoints.
"""

import asyncio

from hueify import Hueify
from hueify.models import LightEvent, ResourceType

# adjust to a light name that exists in your setup
LIGHT_NAME = "Desk"


async def main() -> None:
    async with Hueify() as hue:
        light = await hue.lights.find_by_name(LIGHT_NAME)
        print(f"[before] brightness: {light.brightness}%")

        @hue.on(ResourceType.LIGHT)
        async def on_light_event(event: LightEvent) -> None:
            if event.id == light.id and event.brightness is not None:
                print(f"[event]  brightness: {event.brightness}%")

        await hue.start_stream(timeout=5)

        await hue.lights.set_brightness(light.id, 66)

        await asyncio.sleep(3)

        light = await hue.lights.get_one(light.id)
        print(f"[after]  brightness: {light.brightness}%")


if __name__ == "__main__":
    asyncio.run(main())
