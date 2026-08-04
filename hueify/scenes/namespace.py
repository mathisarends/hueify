from hueify.exceptions import ResourceNotFoundException
from hueify.http import HttpClient
from hueify.scenes.cache import SceneCache
from hueify.scenes.service import Scene


class SceneNamespace:
    def __init__(self, scene_cache: SceneCache, http_client: HttpClient) -> None:
        self._scene_cache = scene_cache
        self._http_client = http_client

    @property
    def names(self) -> list[str]:
        return sorted({s.name for s in self._scene_cache.get_all()})

    def from_name(self, name: str) -> Scene:
        scene_info = self._scene_cache.get_by_name(name)
        if scene_info is None:
            raise ResourceNotFoundException(
                resource_type="scene",
                lookup_name=name,
                suggested_names=self.names,
            )
        return Scene(scene_info=scene_info, client=self._http_client)

    async def activate(self, name: str) -> None:
        scene = self.from_name(name)
        await scene.activate()
