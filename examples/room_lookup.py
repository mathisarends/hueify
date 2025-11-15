from hueify import RoomController
from hueify.shared.cache.lookup import LookupCache


async def main():
    cache1 = LookupCache()
    cache2 = LookupCache()
    print(cache1 is cache2)  # Sollte True sein
    print(id(cache1), id(cache2))  # Sollten gleich sein

    room = await RoomController.from_name("Zimmer 1")
    result = await room.activate_scene("Entspannen")
    print("result", result)
    await asyncio.sleep(2)

    room = await RoomController.from_name("Zimmer 1")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
