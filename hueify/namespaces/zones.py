from hueify.cache.service import LookupCache
from hueify.groups import Zone
from hueify.scenes import Scene
from hueify.shared.resource import ActionResult


class ZoneNamespace:
    def __init__(self, cache: LookupCache) -> None:
        self._cache = cache

    async def get(self, name: str) -> Zone:
        return await Zone.from_name(name, cache=self._cache)

    async def turn_on(self, name: str) -> ActionResult:
        zone = await self.get(name)
        return await zone.turn_on()

    async def turn_off(self, name: str) -> ActionResult:
        zone = await self.get(name)
        return await zone.turn_off()

    async def set_brightness(
        self, name: str, brightness_percentage: float | int
    ) -> ActionResult:
        zone = await self.get(name)
        return await zone.set_brightness_percentage(brightness_percentage)

    async def increase_brightness(
        self, name: str, brightness_percentage: float | int
    ) -> ActionResult:
        zone = await self.get(name)
        return await zone.increase_brightness_percentage(brightness_percentage)

    async def decrease_brightness(
        self, name: str, brightness_percentage: float | int
    ) -> ActionResult:
        zone = await self.get(name)
        return await zone.decrease_brightness_percentage(brightness_percentage)

    async def set_color_temperature(
        self, name: str, color_temperature_percentage: float | int
    ) -> ActionResult:
        zone = await self.get(name)
        return await zone.set_color_temperature_percentage(color_temperature_percentage)

    async def get_brightness(self, name: str) -> float:
        zone = await self.get(name)
        return zone.brightness_percentage

    async def activate_scene(self, name: str, scene_name: str) -> ActionResult:
        zone = await self.get(name)
        return await zone.activate_scene(scene_name)

    async def get_active_scene(self, name: str) -> Scene | None:
        zone = await self.get(name)
        return await zone.get_active_scene()
