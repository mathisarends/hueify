from uuid import UUID

from hueify.http.client import HttpClient
from hueify.scenes.lookup import SceneLookup
from hueify.scenes.models import (
    SceneAction,
    SceneActivationRequest,
    SceneInfo,
    SceneRecall,
)
from hueify.utils.logging import LoggingMixin


class SceneService(LoggingMixin):
    def __init__(
        self, client: HttpClient | None = None, scene_lookup: SceneLookup | None = None
    ) -> None:
        super().__init__()
        self._client = client or HttpClient()
        self._lookup = scene_lookup or SceneLookup(self._client)

    async def find_scene_by_name_in_group(
        self, scene_name: str, group_id: UUID
    ) -> SceneInfo:
        return await self._lookup.find_scene_by_name_in_group(scene_name, group_id)

    async def get_scenes_by_group_id(self, group_id: UUID) -> list[SceneInfo]:
        return await self._lookup.get_scenes_by_group_id(group_id)

    async def get_all_scenes(self) -> list[SceneInfo]:
        return await self._lookup.get_all_scenes()

    async def find_scene_by_name(self, scene_name: str) -> SceneInfo:
        return await self._lookup.find_scene_by_name(scene_name)

    async def activate_scene_by_name(self, scene_name: str) -> SceneInfo:
        scene = await self._find_scene_by_name(scene_name)
        await self.activate_scene_by_id(scene.id)
        self.logger.info(f"Activated scene '{scene_name}' (ID: {scene.id})")
        return scene

    async def _find_scene_by_name(self, scene_name: str) -> SceneInfo:
        return await self._lookup.find_scene_by_name(scene_name)

    async def activate_scene_by_id(self, scene_id: UUID) -> None:
        scene_id_str = str(scene_id)
        request = SceneActivationRequest(recall=SceneRecall(action=SceneAction.ACTIVE))
        await self._client.put(f"scene/{scene_id_str}", data=request)
