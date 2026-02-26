import logging

from hueify.exceptions import ResourceNotFoundException
from hueify.http import HttpClient
from hueify.light.cache import LightCache
from hueify.light.service import Light
from hueify.shared.resource import ActionResult

logger = logging.getLogger(__name__)


class LightNamespace:
    def __init__(self, light_cache: LightCache, http_client: HttpClient) -> None:
        self._light_cache = light_cache
        self._http_client = http_client

    @property
    def names(self) -> list[str]:
        return [light.metadata.name for light in self._light_cache.get_all()]

    def from_name(self, name: str) -> Light:
        cached_info = self._light_cache.get_by_name(name)
        if cached_info is None:
            available = [light.metadata.name for light in self._light_cache.get_all()]
            raise ResourceNotFoundException(
                resource_type="light",
                lookup_name=name,
                suggested_names=available,
            )
        return Light(
            light_info=cached_info, client=self._http_client, cache=self._light_cache
        )

    async def turn_on(self, name: str) -> ActionResult:
        light = self.from_name(name)
        return await light.turn_on()

    async def turn_off(self, name: str) -> ActionResult:
        light = self.from_name(name)
        return await light.turn_off()

    async def set_brightness(
        self, name: str, brightness_percentage: float | int
    ) -> ActionResult:
        light = self.from_name(name)
        return await light.set_brightness(brightness_percentage)

    async def increase_brightness(
        self, name: str, brightness_percentage: float | int
    ) -> ActionResult:
        light = self.from_name(name)
        return await light.increase_brightness(brightness_percentage)

    async def decrease_brightness(
        self, name: str, brightness_percentage: float | int
    ) -> ActionResult:
        light = self.from_name(name)
        return await light.decrease_brightness(brightness_percentage)

    async def set_color_temperature(
        self, name: str, color_temperature_percentage: float | int
    ) -> ActionResult:
        light = self.from_name(name)
        return await light.set_color_temperature(color_temperature_percentage)

    def get_brightness(self, name: str) -> float:
        light = self.from_name(name)
        return light.brightness_percentage
