from hueify.grouped_lights.cache import GroupedLightCache
from hueify.grouped_lights.namespace import GroupNamespace
from hueify.grouped_lights.rooms.cache import RoomCache
from hueify.http import HttpClient
from hueify.scenes.cache import SceneCache


class RoomNamespace(GroupNamespace):
    """Namespace for room-level grouped-light and scene control.

    Accessible as :attr:`Hueify.rooms <hueify.service.Hueify.rooms>`.
    Inherits all control methods from
    :class:`~hueify.grouped_lights.GroupNamespace`.

    ```python
    async with Hueify() as hue:
        await hue.rooms.turn_on("Living Room")
        await hue.rooms.activate_scene("Living Room", "Relax")
    ```
    """

    def __init__(
        self,
        room_cache: RoomCache,
        grouped_light_cache: GroupedLightCache,
        http_client: HttpClient,
        scene_cache: SceneCache,
    ) -> None:
        super().__init__(
            group_cache=room_cache,
            resource_type="room",
            grouped_light_cache=grouped_light_cache,
            http_client=http_client,
            scene_cache=scene_cache,
        )
