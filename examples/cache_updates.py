import asyncio

from hueify import Light, LightLookup, RoomLookup, SceneLookup, ZoneLookup, get_cache


async def main():
    _ = get_cache()

    light_lookup = LightLookup()
    room_lookup = RoomLookup()
    zone_lookup = ZoneLookup()
    scene_lookup = SceneLookup()

    await asyncio.gather(
        light_lookup.get_lights(),
        room_lookup.get_all_entities(),
        zone_lookup.get_all_entities(),
        scene_lookup.get_scenes(),
    )

    light = await Light.from_name("Hue Lightstrip plus 1")
    print("brightness before:", light.current_brightness)

    await asyncio.sleep(10)

    # see wheter cache updated the light state
    light2 = await Light.from_name("Hue Lightstrip plus 1")
    print("brightness after:", light2.current_brightness)


if __name__ == "__main__":
    asyncio.run(main())
