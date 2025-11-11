from hueify.groups.lookup.lookup import GroupLookup
from hueify.groups.service import GroupService

from hueify.groups.rooms import RoomController


lookup = GroupLookup()
group_service = GroupService()

async def main():
    room = await lookup.get_room_by_name("Zimmer 1")
    print(f"Room Info: {room}")

    all_rooms = await lookup.get_rooms()
    for room in all_rooms:
        print(f"Room: {room.name} (ID: {room.id})")


    room_controller = await RoomController.from_name("Zimmer 1")
    await room_controller.activate_scene("Entspannen")



if __name__ == "__main__":
    import asyncio
    asyncio.run(main())