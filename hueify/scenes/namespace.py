import logging
from uuid import UUID

from hueify.groups import RoomNotFoundException, ZoneNotFoundException
from hueify.http import HttpClient
from hueify.room.cache import RoomCache
from hueify.scenes.cache import SceneCache
from hueify.scenes.exceptions import SceneNotFoundException
from hueify.scenes.models import SceneInfo
from hueify.scenes.service import Scene
from hueify.shared.fuzzy import find_all_matches_sorted
from hueify.shared.resource.models import ActionResult
from hueify.zone.cache import ZoneCache

logger = logging.getLogger(__name__)


class SceneNamespace:
    def __init__(
        self,
        scene_cache: SceneCache,
        room_cache: RoomCache,
        zone_cache: ZoneCache,
        http_client: HttpClient,
    ) -> None:
        self._scene_cache = scene_cache
        self._room_cache = room_cache
        self._zone_cache = zone_cache
        self._http_client = http_client

    def scene_names_for_room(self, room_name: str) -> list[str]:
        room_id = self._resolve_room_id(room_name)
        return [s.name for s in self._get_scenes_in_group(room_id)]

    async def activate_in_room(self, scene_name: str, room_name: str) -> ActionResult:
        room_id = self._resolve_room_id(room_name)
        scene_info = self._find_scene_in_group(scene_name, room_id)
        return await Scene(scene_info=scene_info, client=self._http_client).activate()

    async def activate_in_zone(self, scene_name: str, zone_name: str) -> ActionResult:
        zone_id = self._resolve_zone_id(zone_name)
        scene_info = self._find_scene_in_group(scene_name, zone_id)
        return await Scene(scene_info=scene_info, client=self._http_client).activate()

    def get_active_scene_for_room(self, room_name: str) -> SceneInfo | None:
        room_id = self._resolve_room_id(room_name)
        return self._find_active_scene_in_group(room_id)

    def get_active_scene_for_zone(self, zone_name: str) -> SceneInfo | None:
        zone_id = self._resolve_zone_id(zone_name)
        return self._find_active_scene_in_group(zone_id)

    def list_scenes_for_room(self, room_name: str) -> list[SceneInfo]:
        room_id = self._resolve_room_id(room_name)
        return self._get_scenes_in_group(room_id)

    def list_scenes_for_zone(self, zone_name: str) -> list[SceneInfo]:
        zone_id = self._resolve_zone_id(zone_name)
        return self._get_scenes_in_group(zone_id)

    def _resolve_room_id(self, room_name: str) -> UUID:
        room_info = self._room_cache.get_by_name(room_name)
        if room_info is None:
            available = [r.metadata.name for r in self._room_cache.get_all()]
            raise RoomNotFoundException(
                lookup_name=room_name, suggested_names=available
            )
        return room_info.id

    def _resolve_zone_id(self, zone_name: str) -> UUID:
        zone_info = self._zone_cache.get_by_name(zone_name)
        if zone_info is None:
            available = [z.metadata.name for z in self._zone_cache.get_all()]
            raise ZoneNotFoundException(
                lookup_name=zone_name, suggested_names=available
            )
        return zone_info.id

    def _get_scenes_in_group(self, group_id: UUID) -> list[SceneInfo]:
        return [s for s in self._scene_cache.get_all() if s.group_id == group_id]

    def _find_scene_in_group(self, scene_name: str, group_id: UUID) -> SceneInfo:
        group_scenes = self._get_scenes_in_group(group_id)

        for scene in group_scenes:
            if scene.name.lower() == scene_name.lower():
                return scene

        matching_scenes = find_all_matches_sorted(
            query=scene_name,
            items=group_scenes,
            text_extractor=lambda s: s.name,
        )
        raise SceneNotFoundException(
            lookup_name=scene_name,
            suggested_names=[s.name for s in matching_scenes],
        )

    def _find_active_scene_in_group(self, group_id: UUID) -> SceneInfo | None:
        return next(
            (s for s in self._get_scenes_in_group(group_id) if s.is_active),
            None,
        )
