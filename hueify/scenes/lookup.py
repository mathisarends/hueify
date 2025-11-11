from uuid import UUID
from hueify.http.client import HttpClient
from hueify.http.models import ApiResponse
from hueify.scenes.models import SceneInfo, SceneInfoListAdapter
from hueify.scenes.exceptions import SceneNotFoundError
from hueify.utils.fuzzy import find_all_matches


class SceneLookup:
    def __init__(self, client: HttpClient) -> None:
        self._client = client

    async def get_all_scenes(self) -> list[SceneInfo]:
        response = await self._client.get("scene")
        return self._parse_scenes_response(response)

    async def find_scene_by_name(self, scene_name: str) -> SceneInfo:
        all_scenes = await self.get_all_scenes()
        
        for scene in all_scenes:
            if scene.name.lower() == scene_name.lower():
                return scene

        suggestions = find_all_matches(
            query=scene_name,
            items=all_scenes,
            text_extractor=lambda s: s.name,
            min_similarity=0.6
        )

        raise SceneNotFoundError(
            lookup_name=scene_name,
            suggested_names=[s.name for s in suggestions]
        )

    async def find_scene_by_name_in_group(self, scene_name: str, group_id: UUID) -> SceneInfo:
        all_scenes = await self.get_all_scenes()
        group_scenes = [scene for scene in all_scenes if scene.group_id == group_id]
        
        for scene in group_scenes:
            if scene.name.lower() == scene_name.lower():
                return scene

        suggestions = find_all_matches(
            query=scene_name,
            items=group_scenes,
            text_extractor=lambda s: s.name,
            min_similarity=0.6
        )

        raise SceneNotFoundError(
            lookup_name=scene_name,
            suggested_names=[s.name for s in suggestions]
        )

    async def get_scenes_by_group_id(self, group_id: UUID) -> list[SceneInfo]:
        all_scenes = await self.get_all_scenes()
        return [scene for scene in all_scenes if scene.group_id == group_id]

    def _parse_scenes_response(self, response: ApiResponse) -> list[SceneInfo]:
        data = response.get("data", [])
        if not data:
            return []
        
        return SceneInfoListAdapter.validate_python(data)
