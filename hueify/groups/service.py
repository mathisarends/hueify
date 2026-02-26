from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING
from uuid import UUID

from hueify.grouped_lights import GroupedLights
from hueify.groups.models import GroupInfo
from hueify.http import HttpClient
from hueify.scenes.cache import SceneCache
from hueify.scenes.exceptions import SceneNotFoundException
from hueify.scenes.models import SceneInfo
from hueify.scenes.service import Scene
from hueify.shared.fuzzy import find_all_matches_sorted
from hueify.shared.resource.models import (
    ActionResult,
)

if TYPE_CHECKING:
    from hueify.shared.resource import NamedResourceLookup


class Group:
    def __init__(
        self,
        group_info: GroupInfo,
        grouped_lights: GroupedLights,
        client: HttpClient,
        scene_cache: SceneCache | None = None,
    ) -> None:
        self._group_info = group_info
        self._grouped_lights = grouped_lights
        self._client = client
        self._scene_cache = scene_cache

    @classmethod
    @abstractmethod
    def _create_lookup(cls, client: HttpClient) -> NamedResourceLookup:
        pass

    @property
    def id(self) -> UUID:
        return self._group_info.id

    @property
    def name(self) -> str:
        return self._group_info.name

    @property
    def grouped_light_id(self) -> UUID:
        return self._grouped_lights.id

    @property
    def is_on(self) -> bool:
        return self._grouped_lights.is_on

    @property
    def brightness_percentage(self) -> float:
        return self._grouped_lights.brightness_percentage

    @property
    def color_temperature_percentage(self) -> int | None:
        return self._grouped_lights.color_temperature_percentage

    async def turn_on(self) -> ActionResult:
        return await self._grouped_lights.turn_on()

    async def turn_off(self) -> ActionResult:
        return await self._grouped_lights.turn_off()

    async def set_brightness(self, percentage: float | int) -> ActionResult:
        return await self._grouped_lights.set_brightness(percentage)

    async def increase_brightness(self, percentage: float | int) -> ActionResult:
        return await self._grouped_lights.increase_brightness(percentage)

    async def decrease_brightness(self, percentage: float | int) -> ActionResult:
        return await self._grouped_lights.decrease_brightness(percentage)

    async def set_color_temperature(self, percentage: float | int) -> ActionResult:
        return await self._grouped_lights.set_color_temperature(percentage)

    @property
    def scene_names(self) -> list[str]:
        return [s.name for s in self._list_scenes()]

    def list_scenes(self) -> list[SceneInfo]:
        return self._list_scenes()

    def get_active_scene(self) -> SceneInfo | None:
        return next((s for s in self._list_scenes() if s.is_active), None)

    async def activate_scene(self, scene_name: str) -> ActionResult:
        scenes = self._list_scenes()
        scene_info = self._resolve_scene(scene_name, scenes)
        scene = Scene(scene_info=scene_info, client=self._client)
        return await scene.activate()

    def _list_scenes(self) -> list[SceneInfo]:
        if self._scene_cache is None:
            raise ValueError(f"No scene cache available for '{self.name}'")
        return [s for s in self._scene_cache.get_all() if s.group_id == self.id]

    def _resolve_scene(self, scene_name: str, scenes: list[SceneInfo]) -> SceneInfo:
        for scene in scenes:
            if scene.name.lower() == scene_name.lower():
                return scene

        matching_scenes = find_all_matches_sorted(
            query=scene_name,
            items=scenes,
            text_extractor=lambda s: s.name,
        )
        raise SceneNotFoundException(
            lookup_name=scene_name,
            suggested_names=[s.name for s in matching_scenes],
        )
