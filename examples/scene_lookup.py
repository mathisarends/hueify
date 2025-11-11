from hueify.scenes import SceneLookup

async def main():
    scene_lookup = SceneLookup()

    scenes = await scene_lookup.find_scene_by_name("Nachts")
    print(scenes)

if __name__ == "__main__":
    import asyncio

    asyncio.run(main())