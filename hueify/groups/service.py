from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Self
from uuid import UUID

from hueify.grouped_lights import GroupedLights
from hueify.groups.models import GroupInfo
from hueify.http import HttpClient
from hueify.scenes import SceneInfo
from hueify.scenes.exceptions import NoActiveSceneException
from hueify.scenes.lookup import SceneLookup
from hueify.scenes.service import Scene
from hueify.shared.resource.models import (
    ActionResult,
)
from hueify.utils.decorators import time_execution_async
from hueify.utils.logging import LoggingMixin

if TYPE_CHECKING:
    from hueify.shared.resource import NamedResourceLookup


class Group(LoggingMixin):
    def __init__(
        self,
        group_info: GroupInfo,
        grouped_lights: GroupedLights,
        client: HttpClient | None = None,
        scene_lookup: SceneLookup | None = None,
    ) -> None:
        self._group_info = group_info
        self._grouped_lights = grouped_lights
        self._client = client or HttpClient()
        self._scene_lookup = scene_lookup or SceneLookup(client=self._client)

    @classmethod
    @time_execution_async()
    async def from_name(cls, group_name: str, client: HttpClient | None = None) -> Self:
        client = client or HttpClient()
        group_lookup = cls._create_lookup(client)
        group_info = await group_lookup.get_entity_by_name(group_name)

        grouped_light_id = cls._extract_grouped_light_id(group_info)
        grouped_lights = await GroupedLights.from_id(grouped_light_id, client=client)
        await grouped_lights.ensure_event_subscription()

        return cls(group_info=group_info, grouped_lights=grouped_lights, client=client)

    @staticmethod
    def _extract_grouped_light_id(group_info: GroupInfo) -> UUID:
        grouped_light_reference = group_info.get_grouped_light_reference_if_exists()

        if grouped_light_reference is None:
            raise ValueError(
                f"No grouped_light service found for group {group_info.id}"
            )

        return grouped_light_reference

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

    async def set_brightness_percentage(self, percentage: float | int) -> ActionResult:
        return await self._grouped_lights.set_brightness_percentage(percentage)

    async def increase_brightness_percentage(
        self, percentage: float | int
    ) -> ActionResult:
        return await self._grouped_lights.increase_brightness_percentage(percentage)

    async def decrease_brightness_percentage(
        self, percentage: float | int
    ) -> ActionResult:
        return await self._grouped_lights.decrease_brightness_percentage(percentage)

    async def set_color_temperature_percentage(
        self, percentage: float | int
    ) -> ActionResult:
        return await self._grouped_lights.set_color_temperature_percentage(percentage)

    @time_execution_async()
    async def activate_scene(self, scene_name: str) -> ActionResult:
        scene = await Scene.from_name_in_group(
            scene_name=scene_name, group_id=self.id, client=self._client
        )
        return await scene.activate()

    @time_execution_async()
    async def get_scenes(self) -> list[SceneInfo]:
        all_scenes = await self._scene_lookup.get_scenes()
        return [scene for scene in all_scenes if scene.group_id == self.id]

    @time_execution_async()
    async def get_active_scene(self) -> SceneInfo:
        active_scene = await self._scene_lookup.get_active_scene_in_group(self.id)

        if active_scene is None:
            light_info = self._grouped_lights._light_info
            raise NoActiveSceneException(
                group_name=self.name,
                is_light_on=light_info.on.on,
                brightness=light_info.dimming.brightness
                if light_info.dimming
                else None,
            )
        return active_scene
