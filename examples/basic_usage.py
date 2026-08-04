import asyncio

from hueify import Hueify

# adjust to a light name that exists in your setup
LIGHT_NAME = "Desk"


async def main() -> None:
    async with Hueify() as hue:
        for light in (await hue.lights.list()).data:
            print(f"{light.metadata.name}: on={light.on.on}")

        desk = await hue.lights.find_by_name(LIGHT_NAME)

        await hue.lights.turn_on(desk.id, brightness=50)
        await asyncio.sleep(2)

        await hue.lights.set_hex(desk.id, "#ff8800")
        await asyncio.sleep(2)

        await hue.lights.set_color_temperature(desk.id, 2700, transition=2)
        await asyncio.sleep(2)

        print(f"{LIGHT_NAME} is on:", await hue.lights.is_on(desk.id))

        await hue.lights.turn_off(desk.id, transition=1)


if __name__ == "__main__":
    asyncio.run(main())
