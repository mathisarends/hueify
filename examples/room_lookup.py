from hueify import Room


async def main():
    room = await Room.from_name("Zimmer 1")
    await room.turn_on()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
