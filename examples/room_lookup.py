import asyncio

from hueify import Room, get_cache


async def main():
    cache = get_cache()
    await cache.populate()

    room = await Room.from_name("Zimmer 1")

    scene = await room.get_active_scene()

    await room.decrease_brightness_percentage(15)
    print("scene:", scene)

    # await room.turn_off()

    # await asyncio.sleep(5)

    # await room.turn_on()

    # await asyncio.sleep(5)

    # await room.increase_brightness_percentage(30)

    # await asyncio.sleep(5)

    # await room.decrease_brightness_percentage(20)

    print(f"Turned on room: {room.brightness_percentage}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
