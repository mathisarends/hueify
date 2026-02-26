import asyncio

from hueify import Hueify


async def main():
    async with Hueify() as hueify:
        print(hueify.rooms.names)


if __name__ == "__main__":
    asyncio.run(main())
