from hueify.lights import LightController


async def main():
    light_controller = await LightController.from_name("Hue Lightstrip")
    await light_controller.increase_brightness(15)
    await asyncio.sleep(2)
    await light_controller.decrease_brightness(15)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
