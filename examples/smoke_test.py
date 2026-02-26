import asyncio

from hueify import Hueify


async def main():
    async with Hueify() as hue:
        print(hue.rooms.names)
        result = await hue.rooms.activate_scene("Zimmer 1", "Wertvoll")
        print(result)


if __name__ == "__main__":
    asyncio.run(main())
