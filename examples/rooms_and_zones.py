"""Controlling whole rooms and zones instead of single lights.

A room groups devices, a zone groups light services, and both are switched
through their grouped light. hueify resolves that service for you, so rooms
and zones understand the same commands as a single light - in one bridge
call instead of one call per lamp.
"""

import asyncio

from hueify import Hueify

# adjust to names that exist in your setup
ROOM_NAME = "Office"
ZONE_NAME = "Desk area"


async def main() -> None:
    async with Hueify() as hue:
        print("Rooms:", [room.metadata.name for room in (await hue.rooms.list()).data])
        print("Zones:", [zone.metadata.name for zone in (await hue.zones.list()).data])

        office = await hue.rooms.find_by_name(ROOM_NAME)

        for light in await hue.rooms.lights(office.id):
            print(f"  light: {light.metadata.name} (on={light.on.on})")

        for scene in await hue.rooms.scenes(office.id):
            print(f"  scene: {scene.metadata.name}")

        await hue.rooms.turn_on(office.id, brightness=70, transition=1)
        print(f"{ROOM_NAME} is on:", await hue.rooms.is_on(office.id))
        await asyncio.sleep(2)

        await hue.rooms.set_color_temperature(office.id, 2200, transition=2)
        await asyncio.sleep(3)

        await hue.rooms.dim(office.id, by=40)
        await asyncio.sleep(2)

        # zones expose exactly the same commands
        zone = await hue.zones.find_by_name(ZONE_NAME)
        await hue.zones.set_rgb(zone.id, 255, 180, 107, brightness=55)
        await asyncio.sleep(2)

        await hue.rooms.turn_off(office.id, transition=3)
        await hue.zones.turn_off(zone.id, transition=3)


if __name__ == "__main__":
    asyncio.run(main())
