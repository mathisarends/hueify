from hueify import ZoneController


async def main():
    room = await ZoneController.from_name("Ikea Leuchte")
    await room.turn_on()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
