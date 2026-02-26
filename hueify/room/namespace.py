import logging

from hueify.grouped_lights.cache import GroupedLightCache
from hueify.grouped_lights.service import GroupedLights
from hueify.groups import RoomNotFoundException
from hueify.http import HttpClient
from hueify.room.cache import RoomCache
from hueify.scenes.cache import SceneCache
from hueify.scenes.models import SceneInfo
from hueify.shared.resource import ActionResult

logger = logging.getLogger(__name__)


class RoomNamespace:
    def __init__(
        self,
        room_cache: RoomCache,
        grouped_light_cache: GroupedLightCache,
        http_client: HttpClient,
        scene_cache: SceneCache,
    ) -> None:
        self._room_cache = room_cache
        self._grouped_light_cache = grouped_light_cache
        self._http_client = http_client
        self._scene_cache = scene_cache

    @property
    def names(self) -> list[str]:
        return [r.metadata.name for r in self._room_cache.get_all()]

    def from_name(self, name: str) -> GroupedLights:
        group_info = self._room_cache.get_by_name(name)
        if group_info is None:
            available = [r.metadata.name for r in self._room_cache.get_all()]
            raise RoomNotFoundException(lookup_name=name, suggested_names=available)

        grouped_light_id = group_info.get_grouped_light_reference_if_exists()
        if grouped_light_id is None:
            raise ValueError(f"Room '{name}' has no grouped_light service reference")

        grouped_light_info = self._grouped_light_cache.get_by_id(grouped_light_id)
        if grouped_light_info is None:
            raise ValueError(
                f"GroupedLight {grouped_light_id} not in cache for room '{name}'"
            )

        return GroupedLights(
            light_info=grouped_light_info,
            client=self._http_client,
            group_info=group_info,
            scene_cache=self._scene_cache,
        )

    async def turn_on(self, name: str) -> ActionResult:
        room = self.from_name(name)
        return await room.turn_on()

    async def turn_off(self, name: str) -> ActionResult:
        room = self.from_name(name)
        return await room.turn_off()

    async def set_brightness(self, name: str, percentage: float | int) -> ActionResult:
        room = self.from_name(name)
        return await room.set_brightness(percentage)

    async def increase_brightness(
        self, name: str, percentage: float | int
    ) -> ActionResult:
        room = self.from_name(name)
        return await room.increase_brightness(percentage)

    async def decrease_brightness(
        self, name: str, percentage: float | int
    ) -> ActionResult:
        room = self.from_name(name)
        return await room.decrease_brightness(percentage)

    async def set_color_temperature(
        self, name: str, percentage: float | int
    ) -> ActionResult:
        room = self.from_name(name)
        return await room.set_color_temperature(percentage)

    def get_brightness(self, name: str) -> float:
        room = self.from_name(name)
        return room.brightness_percentage

    def scene_names(self, name: str) -> list[str]:
        room = self.from_name(name)
        return room.scene_names

    def list_scenes(self, name: str) -> list[SceneInfo]:
        room = self.from_name(name)
        return room.list_scenes()

    def get_active_scene(self, name: str) -> SceneInfo | None:
        room = self.from_name(name)
        return room.get_active_scene()

    async def activate_scene(self, name: str, scene_name: str) -> ActionResult:
        room = self.from_name(name)
        return await room.activate_scene(scene_name)
