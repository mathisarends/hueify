from hueify.lights import LightController, LightLookup


async def main():
    lookup = LightLookup()
    lights = await lookup.get_lights()

    for light in lights:
        print("light", light)

    light_controller = await LightController.from_name("Hue lightstrip plus 1")
    await light_controller.turn_off()
    await asyncio.sleep(2)
    await light_controller.turn_on()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
