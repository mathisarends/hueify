from hueify.cache.service import LookupCache
from hueify.groups import Room
from hueify.scenes import Scene
from hueify.shared.resource import ActionResult


class RoomNamespace:
    def __init__(self, cache: LookupCache) -> None:
        self._cache = cache

    async def get(self, name: str) -> Room:
        return await Room.from_name(name, cache=self._cache)

    async def turn_on(self, name: str) -> ActionResult:
        room = await self.get(name)
        return await room.turn_on()

    async def turn_off(self, name: str) -> ActionResult:
        room = await self.get(name)
        return await room.turn_off()

    async def set_brightness(
        self, name: str, brightness_percentage: float | int
    ) -> ActionResult:
        room = await self.get(name)
        return await room.set_brightness_percentage(brightness_percentage)

    async def increase_brightness(
        self, name: str, brightness_percentage: float | int
    ) -> ActionResult:
        room = await self.get(name)
        return await room.increase_brightness_percentage(brightness_percentage)

    async def decrease_brightness(
        self, name: str, brightness_percentage: float | int
    ) -> ActionResult:
        room = await self.get(name)
        return await room.decrease_brightness_percentage(brightness_percentage)

    async def set_color_temperature(
        self, name: str, color_temperature_percentage: float | int
    ) -> ActionResult:
        room = await self.get(name)
        return await room.set_color_temperature_percentage(color_temperature_percentage)

    async def get_brightness(self, name: str) -> float:
        room = await self.get(name)
        return room.brightness_percentage

    async def activate_scene(self, name: str, scene_name: str) -> ActionResult:
        room = await self.get(name)
        return await room.activate_scene(scene_name)

    async def get_active_scene(self, name: str) -> Scene | None:
        room = await self.get(name)
        return await room.get_active_scene()
