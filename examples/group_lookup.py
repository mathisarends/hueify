from hueify.groups.lookup.lookup import GroupLookup


lookup = GroupLookup()

async def main():
    room = await lookup.get_room_by_name("Zimmer 1")
    print(f"Room Info: {room}")

    # Get all rooms
    all_rooms = await lookup.get_rooms()
    for room in all_rooms:
        print(f"Room: {room.name} (ID: {room.id})")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())