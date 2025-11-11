
from hueify.groups import RoomController, GroupDiscovery
from hueify.groups.models import GroupType



async def main():
    group_discovery = GroupDiscovery()
    all_groups = await group_discovery.get_all_groups()
    for group in all_groups:
        if group.type == GroupType.ROOM:
            room_controller = RoomController.from_group_info(group)
            await room_controller.activate_scene("Entspannen")
        print(f"Found group: {group.name} (ID: {group.id})")

    # room_controller = await RoomController.from_name("Zimmer 1")
    # await room_controller.activate_scene("Entspannen")



if __name__ == "__main__":
    import asyncio
    asyncio.run(main())