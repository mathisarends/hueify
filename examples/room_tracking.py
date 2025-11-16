from hueify import Room


async def main():
    room = await Room.from_name("Zimmer 1")

    await room.turn_on()

    print("room current brightness:", room.current_brightness_percentage)

    await asyncio.sleep(5)

    print("room current brightness aufter time:", room.current_brightness_percentage)

    print("room current on state:", room.is_on)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
