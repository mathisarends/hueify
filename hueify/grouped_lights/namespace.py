import logging

from hueify.cache.lookup import NamedEntityLookupCache
from hueify.grouped_lights.cache import GroupedLightCache
from hueify.grouped_lights.models import GroupInfo
from hueify.grouped_lights.service import GroupedLights
from hueify.http import HttpClient
from hueify.scenes.cache import SceneCache
from hueify.scenes.schemas import SceneInfo
from hueify.shared.exceptions import ResourceNotFoundException
from hueify.shared.resource import ActionResult

logger = logging.getLogger(__name__)


class GroupNamespace:
    def __init__(
        self,
        group_cache: NamedEntityLookupCache[GroupInfo],
        not_found_exception: type[ResourceNotFoundException],
        grouped_light_cache: GroupedLightCache,
        http_client: HttpClient,
        scene_cache: SceneCache,
    ) -> None:
        self._group_cache = group_cache
        self._not_found_exception = not_found_exception
        self._grouped_light_cache = grouped_light_cache
        self._http_client = http_client
        self._scene_cache = scene_cache

    @property
    def names(self) -> list[str]:
        return [g.metadata.name for g in self._group_cache.get_all()]

    def from_name(self, name: str) -> GroupedLights:
        group_info = self._group_cache.get_by_name(name)
        if group_info is None:
            available = [g.metadata.name for g in self._group_cache.get_all()]
            raise self._not_found_exception(lookup_name=name, suggested_names=available)

        grouped_light_id = group_info.get_grouped_light_reference_if_exists()
        if grouped_light_id is None:
            raise ValueError(f"Group '{name}' has no grouped_light service reference")

        grouped_light_info = self._grouped_light_cache.get_by_id(grouped_light_id)
        if grouped_light_info is None:
            raise ValueError(
                f"GroupedLight {grouped_light_id} not in cache for group '{name}'"
            )

        return GroupedLights(
            light_info=grouped_light_info,
            client=self._http_client,
            group_info=group_info,
            scene_cache=self._scene_cache,
        )

    async def turn_on(self, name: str) -> ActionResult:
        group = self.from_name(name)
        return await group.turn_on()

    async def turn_off(self, name: str) -> ActionResult:
        group = self.from_name(name)
        return await group.turn_off()

    async def set_brightness(self, name: str, percentage: float | int) -> ActionResult:
        group = self.from_name(name)
        return await group.set_brightness(percentage)

    async def increase_brightness(
        self, name: str, percentage: float | int
    ) -> ActionResult:
        group = self.from_name(name)
        return await group.increase_brightness(percentage)

    async def decrease_brightness(
        self, name: str, percentage: float | int
    ) -> ActionResult:
        group = self.from_name(name)
        return await group.decrease_brightness(percentage)

    async def set_color_temperature(
        self, name: str, percentage: float | int
    ) -> ActionResult:
        group = self.from_name(name)
        return await group.set_color_temperature(percentage)

    def get_brightness(self, name: str) -> float:
        group = self.from_name(name)
        return group.brightness_percentage

    def scene_names(self, name: str) -> list[str]:
        group = self.from_name(name)
        return group.scene_names

    def list_scenes(self, name: str) -> list[SceneInfo]:
        group = self.from_name(name)
        return group.list_scenes()

    def get_active_scene(self, name: str) -> SceneInfo | None:
        group = self.from_name(name)
        return group.get_active_scene()

    async def activate_scene(self, name: str, scene_name: str) -> ActionResult:
        group = self.from_name(name)
        return await group.activate_scene(scene_name)
