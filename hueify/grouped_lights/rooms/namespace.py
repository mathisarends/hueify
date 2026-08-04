from hueify.grouped_lights.cache import GroupedLightCache
from hueify.grouped_lights.namespace import GroupNamespace
from hueify.grouped_lights.rooms.cache import RoomCache
from hueify.http import HttpClient
from hueify.scenes.cache import SceneCache


class RoomNamespace(GroupNamespace):
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
