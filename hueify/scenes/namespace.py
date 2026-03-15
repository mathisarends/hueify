from hueify.exceptions import ResourceNotFoundException
from hueify.http import HttpClient
from hueify.scenes.cache import SceneCache
from hueify.scenes.service import Scene


class SceneNamespace:
    """Namespace for bridge-wide scene lookup and activation.

    Accessible as :attr:`Hueify.scenes <hueify.service.Hueify.scenes>`.

    Unlike room/zone namespaces, this namespace operates across all scenes
    known to the bridge regardless of which room or zone they belong to.

    ```python
    async with Hueify() as hue:
        print(hue.scenes.names)           # all scene names
        await hue.scenes.activate("Relax")
    ```
    """

    def __init__(self, scene_cache: SceneCache, http_client: HttpClient) -> None:
        self._scene_cache = scene_cache
        self._http_client = http_client

    @property
    def names(self) -> list[str]:
        return sorted({s.name for s in self._scene_cache.get_all()})

    def from_name(self, name: str) -> Scene:
        """Look up a scene by name and return a :class:`~hueify.scenes.Scene` handle.

        Args:
            name: Exact scene name as configured in the Hue app.

        Raises:
            :class:`~hueify.exceptions.ResourceNotFoundException`: When no
                matching scene is found.
        """
        scene_info = self._scene_cache.get_by_name(name)
        if scene_info is None:
            raise ResourceNotFoundException(
                resource_type="scene",
                lookup_name=name,
                suggested_names=self.names,
            )
        return Scene(scene_info=scene_info, client=self._http_client)

    async def activate(self, name: str) -> None:
        """Activate a scene by name.

        Args:
            name: Exact scene name as configured in the Hue app.

        Raises:
            :class:`~hueify.exceptions.ResourceNotFoundException`: When no
                matching scene is found.
        """
        scene = self.from_name(name)
        await scene.activate()
