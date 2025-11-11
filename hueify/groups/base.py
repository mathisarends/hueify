from abc import ABC, abstractmethod
from typing import Self
from uuid import UUID

from hueify.groups.lookup.models import GroupInfo, GroupInfoListAdapter
from hueify.scenes.models import SceneInfo, SceneStatusValue
from hueify.scenes.service import SceneService
from hueify.http import HttpClient, ApiResponse
from hueify.utils.fuzzy import find_all_matches

class GroupLookup(ABC):
    def __init__(self, client: HttpClient | None = None) -> None:
        self._client = client or HttpClient()

    async def get_group_by_name(self, group_name: str) -> GroupInfo:
        groups = await self._get_all_groups()
        
        for group in groups:
            if group.name.lower() == group_name.lower():
                return group
        
        suggestions = find_all_matches(
            query=group_name,
            items=groups,
            text_extractor=lambda g: g.name,
            min_similarity=0.6
        )

        raise self._create_not_found_exception(
            lookup_name=group_name,
            suggested_names=[s.name for s in suggestions]
        )
    
    async def _get_all_groups(self) -> list[GroupInfo]:
        response = await self._client.get(self._get_endpoint())
        return self._parse_groups_response(response)
    
    @abstractmethod
    def _get_endpoint(self) -> str:
        pass

    @abstractmethod
    def _create_not_found_exception(
        self, 
        lookup_name: str, 
        suggested_names: list[str]
    ) -> Exception:
        pass

    def _parse_groups_response(self, response: ApiResponse) -> list[GroupInfo]:
        data = response.get("data", [])
        if not data:
            return []
        
        return GroupInfoListAdapter.validate_python(data)


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
    @abstractmethod
    def _create_lookup(cls, client: HttpClient) -> GroupLookup:
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