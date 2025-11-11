from abc import ABC, abstractmethod
from typing import Self, TYPE_CHECKING
from uuid import UUID

from hueify.groups.models import GroupInfo
from hueify.scenes.models import SceneInfo, SceneStatusValue
from hueify.scenes.service import SceneService
from hueify.http import HttpClient

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

    @classmethod
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
            if scene.status and scene.status.active == SceneStatusValue.ACTIVE:
                return scene
        
        return None