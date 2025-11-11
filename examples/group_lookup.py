from hueify.groups.lookup.lookup import GroupLookup
from hueify.groups.service import GroupService


lookup = GroupLookup()
group_service = GroupService()

async def main():
    room = await lookup.get_room_by_name("Zimmer 1")
    print(f"Room Info: {room}")

    # Get all rooms

    all_rooms = await lookup.get_rooms()
    for room in all_rooms:
        print(f"Room: {room.name} (ID: {room.id})")

    await group_service.activate_scene_for_room("Zimmer 1", "Entspannen")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())