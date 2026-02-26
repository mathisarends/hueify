from hueify.cache import LookupCache
from hueify.lights import Light
from hueify.shared.resource import ActionResult


class LightNamespace:
    def __init__(self, cache: LookupCache) -> None:
        self._cache = cache

    async def get(self, name: str) -> Light:
        return await Light.from_name(name, cache=self._cache)

    async def turn_on(self, name: str) -> ActionResult:
        light = await self.get(name)
        return await light.turn_on()

    async def turn_off(self, name: str) -> ActionResult:
        light = await self.get(name)
        return await light.turn_off()

    async def set_brightness(
        self, name: str, brightness_percentage: float | int
    ) -> ActionResult:
        light = await self.get(name)
        return await light.set_brightness_percentage(brightness_percentage)

    async def increase_brightness(
        self, name: str, brightness_percentage: float | int
    ) -> ActionResult:
        light = await self.get(name)
        return await light.increase_brightness_percentage(brightness_percentage)

    async def decrease_brightness(
        self, name: str, brightness_percentage: float | int
    ) -> ActionResult:
        light = await self.get(name)
        return await light.decrease_brightness_percentage(brightness_percentage)

    async def set_color_temperature(
        self, name: str, color_temperature_percentage: float | int
    ) -> ActionResult:
        light = await self.get(name)
        return await light.set_color_temperature_percentage(
            color_temperature_percentage
        )

    async def get_brightness(self, name: str) -> float:
        light = await self.get(name)
        return light.brightness_percentage
