"""Finding and playing the scenes stored on the bridge."""

import asyncio

from hueify import Hueify

# adjust to names that exist in your setup
ROOM_NAME = "Office"
SCENE_NAME = "Focus"


async def main() -> None:
    async with Hueify() as hue:
        for scene in (await hue.scenes.list()).data:
            print(f"{scene.metadata.name} (group {scene.group.rtype})")

        # scenes belong to a room or a zone, so ask the group for its scenes
        office = await hue.rooms.find_by_name(ROOM_NAME)
        for scene in await hue.rooms.scenes(office.id):
            print(f"{ROOM_NAME}: {scene.metadata.name}")

        focus = await hue.scenes.find_by_name(SCENE_NAME)

        await hue.scenes.activate(focus.id)
        await asyncio.sleep(3)

        # play the same scene dimmed and fade into it over two seconds
        await hue.scenes.activate(focus.id, brightness=40, transition=2)
        await asyncio.sleep(3)

        # scenes with a palette can cycle through their colors
        await hue.scenes.activate(focus.id, dynamic=True)
        await asyncio.sleep(5)

        await hue.rooms.turn_off(office.id, transition=2)


if __name__ == "__main__":
    asyncio.run(main())
