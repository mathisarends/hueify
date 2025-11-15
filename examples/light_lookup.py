from hueify.lights import LightController


async def main():
    light_controller = await LightController.from_name("Hue Lightstrip plus 1")

    await light_controller.turn_off()

    await asyncio.sleep(5)

    await light_controller.turn_on()

    await light_controller.increase_brightness_percentage(20)

    await asyncio.sleep(5)

    await light_controller.decrease_brightness_percentage(20)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
