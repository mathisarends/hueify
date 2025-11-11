from abc import ABC, abstractmethod
from typing import Self, TYPE_CHECKING
from uuid import UUID

from hueify.scenes import SceneService, SceneInfo, SceneStatusValue
from hueify.groups.models import (
    GroupInfo,
    GroupedLightState,
    OnState,
    DimmingState,
    ColorTemperatureState,
    ResourceType,
)
from hueify.http import HttpClient
from hueify.utils.decorators import time_execution_async

if TYPE_CHECKING:
    from hueify.groups.base import GroupLookup

class GroupController(ABC):
    def __init__(
        self,
        group_info: GroupInfo,
        scene_service: SceneService | None = None,
    ) -> None:
        self._group_info = group_info
        self._scene_service = scene_service or SceneService()
        self._client = HttpClient()
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
    def from_group_info(cls, group_info: GroupInfo, client: HttpClient | None = None) -> Self:
        client = client or HttpClient()
        return cls(
            group_info=group_info,
            scene_service=SceneService(client=client)
        )

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

    @time_execution_async()
    async def activate_scene(self, scene_name: str) -> None:
        scene = await self._scene_service.find_scene_by_name_in_group(
            scene_name, 
            group_id=self.id
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
    
    # TODO: Funktioniert irgendwie leider nicht (ist immer inactive)
    async def get_active_scene_name(self) -> str | None:
        active_scene = await self.get_active_scene()
        if active_scene:
            return active_scene.name
        
    async def turn_on(self) -> None:
        update = GroupedLightState(on=OnState(on=True))
        await self._client.put(f"grouped_light/{self.grouped_light_id}", data=update)

    async def turn_off(self) -> None:
        update = GroupedLightState(on=OnState(on=False))
        await self._client.put(f"grouped_light/{self.grouped_light_id}", data=update)
    
    async def set_brightness(self, brightness: int) -> None:
        update = GroupedLightState(
            on=OnState(on=True),
            dimming=DimmingState(brightness=brightness)
        )
        await self._client.put(f"grouped_light/{self.grouped_light_id}", data=update)
    
    async def set_color_temperature(self, mirek: int) -> None:
        update = GroupedLightState(
            on=OnState(on=True),
            color_temperature=ColorTemperatureState(mirek=mirek)
        )
        await self._client.put(f"grouped_light/{self.grouped_light_id}", data=update)

    async def get_grouped_light_state(self) -> GroupedLightState:
        response = await self._client.get(f"grouped_light/{self.grouped_light_id}")
        data = response.get("data", [])
        if not data:
            raise ValueError(f"No grouped light found for group {self.id}")
        
        return GroupedLightState.model_validate(data[0])
