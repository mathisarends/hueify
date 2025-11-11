from hueify.http.client import HttpClient
from hueify.scenes.models import SceneInfo, SceneInfoListAdapter
from hueify.scenes.exceptions import SceneNotFoundError

class SceneLookup:
    def __init__(self, client: HttpClient | None = None) -> None:
        self._client = client or HttpClient()

    async def get_scenes_by_group_id(self, group_id: str) -> list[SceneInfo]:
        all_scenes = await self.get_all_scenes()
        return [
            scene
            for scene in all_scenes
            if scene.group_id == group_id
        ]

    async def find_scene_by_name(self, scene_name: str) -> SceneInfo:
        scenes = await self.get_all_scenes()

        for scene in scenes:
            if scene.name == scene_name:
                return scene

        raise SceneNotFoundError(f"Scene '{scene_name}' not found")

    async def get_all_scenes(self) -> list[SceneInfo]:
        response_dict = await self._client.get("scenes")

        scenes_data = [
            {**scene_data, "id": scene_id}
            for scene_id, scene_data in response_dict.items()
        ]
        return SceneInfoListAdapter.validate_python(scenes_data)