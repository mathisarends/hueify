from uuid import UUID

from hueify.http.client import HttpClient
from hueify.scenes.exceptions import SceneNotFoundException
from hueify.scenes.models import SceneInfo, SceneStatusValue
from hueify.utils.fuzzy import find_all_matches_sorted


class SceneLookup:
    def __init__(self, client: HttpClient | None = None) -> None:
        self._client = client or HttpClient()

    async def get_active_scene(self) -> SceneInfo | None:
        scenes = await self.get_scenes()
        for scene in scenes:
            if scene.status.active != SceneStatusValue.INACTIVE:
                return scene
        return None

    async def get_scenes(self) -> list[SceneInfo]:
        return await self._client.get_resources("scene", SceneInfo)

    async def find_scene_by_name(self, scene_name: str) -> SceneInfo:
        all_scenes = await self.get_scenes()

        for scene in all_scenes:
            if scene.name.lower() == scene_name.lower():
                return scene

        matching_scenes = find_all_matches_sorted(
            query=scene_name,
            items=all_scenes,
            text_extractor=lambda s: s.name,
        )

        suggestions = [scene.name for scene in matching_scenes]

        raise SceneNotFoundException(
            lookup_name=scene_name, suggested_names=suggestions
        )

    async def find_scene_by_name_in_group(
        self, scene_name: str, group_id: UUID
    ) -> SceneInfo:
        all_scenes = await self.get_scenes()
        group_scenes = [scene for scene in all_scenes if scene.group_id == group_id]

        for scene in group_scenes:
            if scene.name.lower() == scene_name.lower():
                return scene

        matching_scenes = find_all_matches_sorted(
            query=scene_name,
            items=group_scenes,
            text_extractor=lambda s: s.name,
        )

        suggestions = [scene.name for scene in matching_scenes]

        raise SceneNotFoundException(
            lookup_name=scene_name, suggested_names=suggestions
        )

    async def get_scenes_by_group_id(self, group_id: UUID) -> list[SceneInfo]:
        all_scenes = await self.get_scenes()
        return [scene for scene in all_scenes if scene.group_id == group_id]
