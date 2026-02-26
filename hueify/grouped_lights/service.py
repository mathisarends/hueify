from pydantic import BaseModel

from hueify.grouped_lights.models import GroupedLightInfo, GroupInfo
from hueify.http import HttpClient
from hueify.scenes.cache import SceneCache
from hueify.scenes.exceptions import SceneNotFoundException
from hueify.scenes.models import SceneInfo
from hueify.scenes.service import Scene
from hueify.shared.fuzzy import find_all_matches_sorted
from hueify.shared.resource import Resource
from hueify.shared.resource.models import ActionResult


class GroupedLights(Resource[GroupedLightInfo]):
    def __init__(
        self,
        light_info: GroupedLightInfo,
        client: HttpClient,
        group_info: GroupInfo | None = None,
        scene_cache: SceneCache | None = None,
    ) -> None:
        super().__init__(light_info=light_info, client=client)
        self._group_info = group_info
        self._scene_cache = scene_cache

    @property
    def name(self) -> str:
        if self._group_info is not None:
            return self._group_info.name
        return self._light_info.name

    def _get_resource_endpoint(self) -> str:
        return "grouped_light"

    async def _update_remote_state(self, state: BaseModel) -> None:
        endpoint = self._get_resource_endpoint()
        await self._client.put(f"{endpoint}/{self.id}", data=state)

    @property
    def scene_names(self) -> list[str]:
        return [s.name for s in self._list_scenes()]

    def list_scenes(self) -> list[SceneInfo]:
        return self._list_scenes()

    def get_active_scene(self) -> SceneInfo | None:
        return next((s for s in self._list_scenes() if s.is_active), None)

    async def activate_scene(self, scene_name: str) -> ActionResult:
        scenes = self._list_scenes()
        scene_info = self._resolve_scene(scene_name, scenes)
        scene = Scene(scene_info=scene_info, client=self._client)
        return await scene.activate()

    def _list_scenes(self) -> list[SceneInfo]:
        if self._scene_cache is None or self._group_info is None:
            raise ValueError(
                f"No scene cache or group info available for '{self.name}'"
            )
        return [
            s for s in self._scene_cache.get_all() if s.group_id == self._group_info.id
        ]

    def _resolve_scene(self, scene_name: str, scenes: list[SceneInfo]) -> SceneInfo:
        for scene in scenes:
            if scene.name.lower() == scene_name.lower():
                return scene

        matching_scenes = find_all_matches_sorted(
            query=scene_name,
            items=scenes,
            text_extractor=lambda s: s.name,
        )
        raise SceneNotFoundException(
            lookup_name=scene_name,
            suggested_names=[s.name for s in matching_scenes],
        )
