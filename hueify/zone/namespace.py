import logging

from hueify.grouped_lights.cache import GroupedLightCache
from hueify.grouped_lights.service import GroupedLights
from hueify.groups import Zone, ZoneNotFoundException
from hueify.http import HttpClient
from hueify.scenes.cache import SceneCache
from hueify.scenes.models import SceneInfo
from hueify.shared.resource import ActionResult
from hueify.zone.cache import ZoneCache

logger = logging.getLogger(__name__)


class ZoneNamespace:
    def __init__(
        self,
        zone_cache: ZoneCache,
        grouped_light_cache: GroupedLightCache,
        http_client: HttpClient,
        scene_cache: SceneCache,
    ) -> None:
        self._zone_cache = zone_cache
        self._grouped_light_cache = grouped_light_cache
        self._http_client = http_client
        self._scene_cache = scene_cache

    @property
    def names(self) -> list[str]:
        return [z.metadata.name for z in self._zone_cache.get_all()]

    async def turn_on(self, name: str) -> ActionResult:
        zone = self.get_zone(name)
        return await zone.turn_on()

    async def turn_off(self, name: str) -> ActionResult:
        zone = self.get_zone(name)
        return await zone.turn_off()

    async def set_brightness(self, name: str, percentage: float | int) -> ActionResult:
        zone = self.get_zone(name)
        return await zone.set_brightness(percentage)

    async def increase_brightness(
        self, name: str, percentage: float | int
    ) -> ActionResult:
        zone = self.get_zone(name)
        return await zone.increase_brightness(percentage)

    async def decrease_brightness(
        self, name: str, percentage: float | int
    ) -> ActionResult:
        zone = self.get_zone(name)
        return await zone.decrease_brightness(percentage)

    async def set_color_temperature(
        self, name: str, percentage: float | int
    ) -> ActionResult:
        zone = self.get_zone(name)
        return await zone.set_color_temperature(percentage)

    def get_brightness(self, name: str) -> float:
        zone = self.get_zone(name)
        return zone.brightness_percentage

    def scene_names(self, name: str) -> list[str]:
        zone = self.get_zone(name)
        return zone.scene_names

    def list_scenes(self, name: str) -> list[SceneInfo]:
        zone = self.get_zone(name)
        return zone.list_scenes()

    def get_active_scene(self, name: str) -> SceneInfo | None:
        zone = self.get_zone(name)
        return zone.get_active_scene()

    async def activate_scene(self, name: str, scene_name: str) -> ActionResult:
        zone = self.get_zone(name)
        return await zone.activate_scene(scene_name)

    def get_zone(self, name: str) -> Zone:
        group_info = self._zone_cache.get_by_name(name)
        if group_info is None:
            available = [z.metadata.name for z in self._zone_cache.get_all()]
            raise ZoneNotFoundException(lookup_name=name, suggested_names=available)

        grouped_light_id = group_info.get_grouped_light_reference_if_exists()
        if grouped_light_id is None:
            raise ValueError(f"Zone '{name}' has no grouped_light service reference")

        grouped_light_info = self._grouped_light_cache.get_by_id(grouped_light_id)
        if grouped_light_info is None:
            raise ValueError(
                f"GroupedLight {grouped_light_id} not in cache for zone '{name}'"
            )

        grouped_lights = GroupedLights(
            light_info=grouped_light_info, client=self._http_client
        )
        return Zone(
            group_info=group_info,
            grouped_lights=grouped_lights,
            client=self._http_client,
            scene_cache=self._scene_cache,
        )
