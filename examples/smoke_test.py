import asyncio

from hueify import Hueify


async def main():
    async with Hueify() as hueify:
        print(hueify.rooms.names)
        await hueify.rooms.turn_on("Zimmer 1")


if __name__ == "__main__":
    asyncio.run(main())
