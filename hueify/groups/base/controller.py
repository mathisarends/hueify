from abc import abstractmethod
from typing import TYPE_CHECKING, Self
from uuid import UUID

from pydantic import BaseModel

from hueify.groups.base.exceptions import NotInColorTemperatureModeError
from hueify.groups.models import (
    ColorTemperatureState,
    GroupedLightDimmingState,
    GroupedLightState,
    GroupInfo,
)
from hueify.http import HttpClient
from hueify.scenes import SceneInfo, SceneService, SceneStatusValue
from hueify.shared.controllers.base import ResourceController
from hueify.shared.types import LightOnState, ResourceType
from hueify.utils.decorators import time_execution_async

if TYPE_CHECKING:
    from hueify.groups.base import GroupLookup


class GroupController(ResourceController):
    def __init__(
        self,
        group_info: GroupInfo,
        client: HttpClient | None = None,
        scene_service: SceneService | None = None,
    ) -> None:
        super().__init__(client)
        self._group_info = group_info
        self._scene_service = scene_service or SceneService(client=self._client)
        self._grouped_light_id = self._extract_grouped_light_id()

    def _extract_grouped_light_id(self) -> UUID:
        for service in self._group_info.services:
            if service.rtype == ResourceType.GROUPED_LIGHT:
                return service.rid

        raise ValueError(f"No grouped_light service found for group {self.id}")

    @classmethod
    @time_execution_async()
    async def from_name(cls, group_name: str, client: HttpClient | None = None) -> Self:
        client = client or HttpClient()
        lookup = cls._create_lookup(client)
        group_info = await lookup.get_group_by_name(group_name)

        return cls(group_info=group_info, scene_service=SceneService(client=client))

    @classmethod
    def from_dto(cls, group_info: GroupInfo, client: HttpClient | None = None) -> Self:
        return cls(group_info=group_info, client=client)

    @classmethod
    @abstractmethod
    def _create_lookup(cls, client: HttpClient) -> "GroupLookup":
        pass

    @property
    def id(self) -> UUID:
        return self._group_info.id

    @property
    def name(self) -> str:
        return self._group_info.name

    @property
    def grouped_light_id(self) -> UUID:
        return self._grouped_light_id

    def _get_resource_endpoint(self) -> str:
        return "grouped_light"

    async def _get_current_brightness(self) -> float:
        state = await self._get_grouped_light_state()
        return state.dimming.brightness if state.dimming else 0.0

    def _create_on_state(self) -> BaseModel:
        return GroupedLightState(on=LightOnState(on=True))

    def _create_off_state(self) -> BaseModel:
        return GroupedLightState(on=LightOnState(on=False))

    def _create_brightness_state(self, brightness: int) -> BaseModel:
        return GroupedLightState(
            on=LightOnState(on=True),
            dimming=GroupedLightDimmingState(brightness=brightness),
        )

    def _create_color_temperature_state(self, mirek: int) -> BaseModel:
        return GroupedLightState(
            on=LightOnState(on=True),
            color_temperature=ColorTemperatureState(mirek=mirek),
        )

    @time_execution_async()
    async def activate_scene(self, scene_name: str) -> None:
        scene = await self._scene_service.find_scene_by_name_in_group(
            scene_name, group_id=self.id
        )
        await self._scene_service.activate_scene_by_id(scene.id)

    async def get_scenes(self) -> list[SceneInfo]:
        return await self._scene_service.get_scenes_by_group_id(self.id)

    async def get_active_scene(self) -> SceneInfo | None:
        scenes = await self.get_scenes()

        for scene in scenes:
            print(scene.status)
            if scene.status and scene.status.active == SceneStatusValue.STATIC:
                return scene

    async def get_active_scene_name(self) -> str | None:
        active_scene = await self.get_active_scene()
        if active_scene:
            return active_scene.name

    def _get_current_mirek(self, state: GroupedLightState) -> int:
        if not state.color_temperature or state.color_temperature.mirek is None:
            raise NotInColorTemperatureModeError(self.name)

        return state.color_temperature.mirek

    async def _get_grouped_light_state(self) -> GroupedLightState:
        return await self._client.get_resource(
            f"grouped_light/{self.grouped_light_id}", resource_type=GroupedLightState
        )
