from hueify.groups.rooms.lookup import RoomLookup
from hueify.groups.zones.lookup import ZoneLookup
from hueify.lights.lookup import LightLookup


async def main():
    light_lookup = LightLookup()
    room_lookup = RoomLookup()
    zone_lookup = ZoneLookup()

    lights_task = light_lookup.get_light_names()
    rooms_task = room_lookup.get_all_entities()
    zones_task = zone_lookup.get_all_entities()

    lights, rooms, zones = await asyncio.gather(lights_task, rooms_task, zones_task)

    light_names = lights
    room_names = [room.name for room in rooms]
    zone_names = [zone.name for zone in zones]

    result = (
        "Lights:\n"
        + "\n".join(light_names)
        + "\n\n"
        + "Rooms:\n"
        + "\n".join(room_names)
        + "\n\n"
        + "Zones:\n"
        + "\n".join(zone_names)
        + "\n\n"
    )
    print("result", result)
    return result


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
