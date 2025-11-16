from hueify.lights import Light


async def main():
    light = await Light.from_name("Hue Lightstrip plus 1")

    await light.turn_on()

    await asyncio.sleep(10)

    print("current brightness:", light.current_brightness)

    print("current on state:", light.is_on)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
