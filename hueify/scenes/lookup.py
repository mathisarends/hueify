from uuid import UUID

from hueify.http import ApiResponse
from hueify.scenes.exceptions import SceneNotFoundException
from hueify.scenes.models import SceneInfo, SceneStatusValue
from hueify.shared.resource.lookup import ResourceLookup
from hueify.shared.resource.models import ResourceType
from hueify.utils.fuzzy import find_all_matches_sorted


class SceneLookup(ResourceLookup[SceneInfo]):
    def get_resource_type(self) -> ResourceType:
        return ResourceType.SCENE

    def _get_endpoint(self) -> str:
        return "scene"

    def _parse_response(self, response: ApiResponse) -> list[SceneInfo]:
        data = response.get("data", [])
        if not data:
            return []

        from pydantic import TypeAdapter

        adapter = TypeAdapter(list[SceneInfo])
        return adapter.validate_python(data)

    def _create_not_found_exception(
        self, lookup_name: str, suggested_names: list[str]
    ) -> Exception:
        return SceneNotFoundException(
            lookup_name=lookup_name, suggested_names=suggested_names
        )

    async def get_active_scene(self) -> SceneInfo | None:
        scenes = await self.get_scenes()
        for scene in scenes:
            if scene.status.active != SceneStatusValue.INACTIVE:
                return scene
        return None

    async def get_scenes(self) -> list[SceneInfo]:
        return await self.get_all_entities()

    async def find_scene_by_name(self, scene_name: str) -> SceneInfo:
        return await self.get_entity_by_name(scene_name)

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
