"""
Demonstrates reacting to bridge changes in real time via the event stream.

Hueify is a stateless, JSON-first client: resources returned by list()/get()
are snapshots that go stale the moment something changes. To learn about updates
as they happen (including ones made by other apps or physical switches), subscribe
to hue.events instead of re-polling the REST endpoints.
"""

import asyncio

from hueify import Hueify, LightUpdate
from hueify.models import DimmingState, LightEvent, OnState, ResourceType

# adjust with a valid light id for you
LIGHT_ID = "ab859e4a-eb52-4984-90bb-9931386d9ef8"


async def main() -> None:
    async with Hueify() as hue:
        light = (await hue.lights.get(LIGHT_ID)).data[0]
        before = light.dimming.brightness if light.dimming else None
        print(f"[before] brightness: {before}%")

        @hue.on(ResourceType.LIGHT)
        async def on_light_event(event: LightEvent) -> None:
            if event.id == light.id and event.dimming is not None:
                print(f"[event]  brightness: {event.dimming.brightness}%")

        await hue.events.connect()
        await asyncio.sleep(1)  # give the SSE connection time to establish

        await hue.lights.update(
            LIGHT_ID,
            LightUpdate(on=OnState(on=True), dimming=DimmingState(brightness=20)),
        )

        await asyncio.sleep(2)

        light = (await hue.lights.get(LIGHT_ID)).data[0]
        after = light.dimming.brightness if light.dimming else None
        print(f"[after]  brightness: {after}%")


if __name__ == "__main__":
    asyncio.run(main())
