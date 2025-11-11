from hueify.groups import RoomController, GroupDiscovery
from hueify.groups.models import GroupType


async def main():
    group_discovery = GroupDiscovery()

    room_controller = await RoomController.from_name("Zimmer 1")
    # await room_controller.activate_scene("Entspannen")

    activate_scene = await room_controller.get_active_scene_name()
    print("Active scene:", activate_scene)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())