from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Self
from uuid import UUID

from pydantic import BaseModel

from hueify.grouped_lights import GroupedLights, GroupedLightState
from hueify.groups.models import GroupInfo
from hueify.http import HttpClient
from hueify.scenes import SceneInfo
from hueify.scenes.controller import SceneController
from hueify.scenes.lookup import SceneLookup
from hueify.shared.resource.base import Resource
from hueify.shared.resource.models import (
    ActionResult,
    ResourceType,
)
from hueify.sse import get_event_bus
from hueify.utils.decorators import time_execution_async

if TYPE_CHECKING:
    from hueify.shared.resource import ResourceLookup


class Group(Resource[GroupedLightState]):
    def __init__(
        self,
        group_info: GroupInfo,
        state: GroupedLightState,
        client: HttpClient | None = None,
        scene_lookup: SceneLookup | None = None,
    ) -> None:
        super().__init__(state, client)
        self._group_info = group_info
        self._scene_lookup = scene_lookup or SceneLookup(client=self._client)
        self._grouped_light_id = self._extract_grouped_light_id(group_info)

    @classmethod
    @time_execution_async()
    async def from_name(cls, group_name: str, client: HttpClient | None = None) -> Self:
        client = client or HttpClient()
        group_lookup = cls._create_lookup(client)
        group_info = await group_lookup.get_entity_by_name(group_name)

        grouped_light_id = cls._extract_grouped_light_id(group_info)
        grouped_lights = await GroupedLights.from_id(grouped_light_id, client=client)

        instance = cls(group_info=group_info, state=grouped_lights.state, client=client)
        await instance.ensure_event_subscription()
        return instance

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
        return self._grouped_light_id

    def _get_resource_endpoint(self) -> str:
        return "grouped_light"

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
