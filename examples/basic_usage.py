import asyncio

from hueify import Hueify, LightUpdate
from hueify.models import DimmingState, OnState

# adjust with a valid light id for you
LIGHT_ID = "ab859e4a-eb52-4984-90bb-9931386d9ef8"


async def main() -> None:
    async with Hueify() as hue:
        lights = (await hue.lights.list()).data
        rooms = (await hue.rooms.list()).data
        zones = (await hue.zones.list()).data

        print("Lights:", [light.id for light in lights])
        print("Rooms:", [room.id for room in rooms])
        print("Zones:", [zone.id for zone in zones])

        light = (await hue.lights.get(LIGHT_ID)).data[0]
        print(f"Light: {light}")

        await hue.lights.update(
            LIGHT_ID,
            LightUpdate(on=OnState(on=True), dimming=DimmingState(brightness=50)),
        )

        await asyncio.sleep(10)

        light = (await hue.lights.get(LIGHT_ID)).data[0]
        brightness = light.dimming.brightness if light.dimming else None
        print("light brightness:", brightness)


if __name__ == "__main__":
    asyncio.run(main())
