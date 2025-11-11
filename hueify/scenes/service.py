from uuid import UUID
from hueify.http.client import HttpClient
from hueify.http.models import ApiResponse
from hueify.scenes.models import (
    SceneActivationRequest,
    SceneInfo,
    SceneInfoListAdapter,
    SceneRecall,
    SceneAction,
)
from hueify.scenes.exceptions import SceneNotFoundError
from hueify.utils.logging import LoggingMixin
from hueify.utils.fuzzy import find_all_matches


class SceneService(LoggingMixin):
    def __init__(self, client: HttpClient | None = None) -> None:
        super().__init__()
        self._client = client or HttpClient()

    async def find_scene_by_name(self, scene_name: str) -> SceneInfo:
        scenes = await self.get_all_scenes()

        for scene in scenes:
            if scene.name.lower() == scene_name.lower():
                return scene

        suggestions = find_all_matches(
            query=scene_name,
            items=scenes,
            text_extractor=lambda s: s.name,
            min_similarity=0.6
        )

        raise SceneNotFoundError(
            lookup_name=scene_name,
            suggested_names=[s.name for s in suggestions]
        )

    async def activate_scene_by_name(self, scene_name: str) -> SceneInfo:
        scene = await self.find_scene_by_name(scene_name)
        await self._activate_scene(scene.id)
        self.logger.info(f"Activated scene '{scene_name}' (ID: {scene.id})")
        return scene

    async def _activate_scene(self, scene_id: UUID) -> None:
        scene_id_str = str(scene_id)
        request = SceneActivationRequest(
            recall=SceneRecall(action=SceneAction.ACTIVE)
        )
        await self._client.put(f"scene/{scene_id_str}", data=request)

    async def get_all_scenes(self) -> list[SceneInfo]:
        response = await self._client.get("scene")
        return self._parse_scenes_response(response)

    def _parse_scenes_response(self, response: ApiResponse) -> list[SceneInfo]:
        data = response.get("data", [])
        if not data:
            return []
        
        return SceneInfoListAdapter.validate_python(data)

