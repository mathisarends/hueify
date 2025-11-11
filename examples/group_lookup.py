from hueify.groups import RoomController


async def main():
    room_controller = await RoomController.from_name("Zimmer 1")
    await room_controller.increase_brightness(15)
    activate_scene = await room_controller.get_active_scene_name()
    print("Active scene:", activate_scene)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
