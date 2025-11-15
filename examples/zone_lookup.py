from hueify import Zone


async def main():
    room = await Zone.from_name("Ikea Leuchte")
    await room.turn_on()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
