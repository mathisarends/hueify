from hueify import LightLookup, Room, RoomLookup, SceneLookup, ZoneLookup, get_cache


async def main():
    _ = get_cache()

    light_lookup = LightLookup()
    room_lookup = RoomLookup()
    zone_lookup = ZoneLookup()
    scene_lookup = SceneLookup()

    await asyncio.gather(
        light_lookup.get_lights(),
        room_lookup.get_all_entities(),
        zone_lookup.get_all_entities(),
        scene_lookup.get_scenes(),
    )

    room = await Room.from_name("Zimmer 1")
    await room.turn_on()

    print(f"Turned on room: {room.brightness_percentage}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
