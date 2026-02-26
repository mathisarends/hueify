from hueify.grouped_lights.cache import GroupedLightCache
from hueify.grouped_lights.exceptions import ZoneNotFoundException
from hueify.grouped_lights.namespace import GroupNamespace
from hueify.grouped_lights.zones.cache import ZoneCache
from hueify.http import HttpClient
from hueify.scenes.cache import SceneCache


class ZoneNamespace(GroupNamespace):
    def __init__(
        self,
        zone_cache: ZoneCache,
        grouped_light_cache: GroupedLightCache,
        http_client: HttpClient,
        scene_cache: SceneCache,
    ) -> None:
        super().__init__(
            group_cache=zone_cache,
            not_found_exception=ZoneNotFoundException,
            grouped_light_cache=grouped_light_cache,
            http_client=http_client,
            scene_cache=scene_cache,
        )
