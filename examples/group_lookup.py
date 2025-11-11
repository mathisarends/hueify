from hueify.groups import RoomController, GroupDiscovery
from hueify.groups.models import GroupType


async def main():
    group_discovery = GroupDiscovery()

    room_controller = await RoomController.from_name("Zimmer 1")

    await room_controller.turn_on()

    await room_controller.turn_off()
    await asyncio.sleep(2)

    await room_controller.turn_on()

    activate_scene = await room_controller.get_active_scene_name()
    print("Active scene:", activate_scene)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())