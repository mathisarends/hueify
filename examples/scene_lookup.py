from hueify.scenes.service import SceneService


async def main():
    scene_lookup = SceneService()
    scenes = await scene_lookup.activate_scene_by_name("Morgendämmerung")
    print(scenes)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
