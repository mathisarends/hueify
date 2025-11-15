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
from hueify.scenes import SceneInfo
from hueify.scenes.controller import SceneController
from hueify.scenes.lookup import SceneLookup
from hueify.shared.controller.base import ResourceController
from hueify.shared.controller.models import ActionResult
from hueify.shared.types import LightOnState, ResourceType
from hueify.utils.decorators import time_execution_async

if TYPE_CHECKING:
    from hueify.groups.base import ResourceLookup


class GroupController(ResourceController):
    def __init__(
        self,
        group_info: GroupInfo,
        state: GroupedLightState,
        client: HttpClient | None = None,
        scene_lookup: SceneLookup | None = None,
    ) -> None:
        super().__init__(client)
        self._group_info = group_info
        self._state = state
        self._scene_lookup = scene_lookup or SceneLookup(client=self._client)
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
        group_lookup = cls._create_lookup(client)
        group_info = await group_lookup.get_entity_by_name(group_name)

        temp_controller = cls.__new__(cls)
        temp_controller._group_info = group_info
        grouped_light_id = temp_controller._extract_grouped_light_id()

        state = await client.get_resource(
            f"grouped_light/{grouped_light_id}", resource_type=GroupedLightState
        )

        return cls(group_info=group_info, state=state, client=client)

    @classmethod
    @abstractmethod
    def _create_lookup(cls, client: HttpClient) -> "ResourceLookup":
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

    @property
    def is_on(self) -> bool:
        return self._state.on.on

    @property
    def current_brightness(self) -> float:
        return self._state.dimming.brightness if self._state.dimming else 0.0

    @property
    def current_color_temperature(self) -> int | None:
        if self._state.color_temperature:
            return self._state.color_temperature.mirek
        return None

    def _get_resource_endpoint(self) -> str:
        return "grouped_light"

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
    async def activate_scene(self, scene_name: str) -> ActionResult:
        scene_controller = await SceneController.from_name_in_group(
            scene_name=scene_name, group_id=self.id, client=self._client
        )
        return await scene_controller.activate()

    @time_execution_async()
    async def get_scenes(self) -> list[SceneInfo]:
        all_scenes = await self._scene_lookup.get_scenes()
        return [scene for scene in all_scenes if scene.group_id == self.id]

    def _get_current_mirek(self, state: GroupedLightState) -> int:
        if not state.color_temperature or state.color_temperature.mirek is None:
            raise NotInColorTemperatureModeError(self.name)

        return state.color_temperature.mirek

    async def _get_grouped_light_state(self) -> GroupedLightState:
        return await self._client.get_resource(
            f"grouped_light/{self.grouped_light_id}", resource_type=GroupedLightState
        )

    async def _update_state(self, state: BaseModel) -> None:
        endpoint = self._get_resource_endpoint()
        await self._client.put(f"{endpoint}/{self.grouped_light_id}", data=state)
        self._state = await self._get_grouped_light_state()
