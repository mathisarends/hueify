from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Self
from uuid import UUID

from pydantic import BaseModel

from hueify.grouped_lights import GroupedLights
from hueify.groups.models import GroupInfo
from hueify.http import HttpClient
from hueify.scenes import SceneInfo
from hueify.scenes.controller import SceneController
from hueify.scenes.lookup import SceneLookup
from hueify.shared.resource.models import (
    ActionResult,
    ResourceType,
)
from hueify.sse.events.bus import get_event_bus
from hueify.utils.decorators import time_execution_async
from hueify.utils.logging import LoggingMixin

if TYPE_CHECKING:
    from hueify.shared.resource import ResourceLookup


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
        for service in group_info.services:
            if service.rtype == ResourceType.GROUPED_LIGHT:
                return service.rid

        raise ValueError(f"No grouped_light service found for group {group_info.id}")

    @classmethod
    @abstractmethod
    def _create_lookup(cls, client: HttpClient) -> ResourceLookup:
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
        scene_controller = await SceneController.from_name_in_group(
            scene_name=scene_name, group_id=self.id, client=self._client
        )
        return await scene_controller.activate()

    @time_execution_async()
    async def get_scenes(self) -> list[SceneInfo]:
        all_scenes = await self._scene_lookup.get_scenes()
        return [scene for scene in all_scenes if scene.group_id == self.id]

    async def _update_remote_state(self, state: BaseModel) -> None:
        endpoint = self._get_resource_endpoint()
        await self._client.put(f"{endpoint}/{self.grouped_light_id}", data=state)

    async def _subscribe_to_events(self) -> None:
        event_bus = await get_event_bus()
        event_bus.subscribe_to_grouped_light(
            handler=self._handle_event,
            group_id=self.grouped_light_id,
        )
