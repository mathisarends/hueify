from hueify import Room, ZoneLookup


async def main():
    room = await Room.from_name("Zimmer 1")
    result = await room.activate_scene("Entspannen")
    print("result", result)
    await asyncio.sleep(2)

    zone_lookup = ZoneLookup()
    zones = await zone_lookup.get_all_entities()
    for zone in zones:
        print(f"Zone: {zone.name} (ID: {zone.id})")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
