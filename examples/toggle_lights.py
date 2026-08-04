import asyncio

from hueify import Hueify, LightUpdate
from hueify.models import DimmingState, OnState

# adjust with a valid light id for you
LIGHT_ID = "ab859e4a-eb52-4984-90bb-9931386d9ef8"
# adjust with a valid scene id for you
SCENE_ID = "630f2ea8-e4fe-4351-914a-56ffd8dd9cd6"


async def main() -> None:
    async with Hueify() as hue:
        light = (await hue.lights.get(LIGHT_ID)).data[0]
        print(f"Light: {light}")

        await hue.lights.update(LIGHT_ID, LightUpdate(on=OnState(on=False)))
        await hue.lights.update(LIGHT_ID, LightUpdate(on=OnState(on=True)))
        await hue.lights.update(
            LIGHT_ID, LightUpdate(dimming=DimmingState(brightness=50))
        )

        await asyncio.sleep(5)

        await hue.scenes.recall(SCENE_ID)

        await asyncio.sleep(5)

        light = (await hue.lights.get(LIGHT_ID)).data[0]
        brightness = light.dimming.brightness if light.dimming else None
        print("light brightness:", brightness)


if __name__ == "__main__":
    asyncio.run(main())
