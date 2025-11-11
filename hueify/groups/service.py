from hueify.http.client import HttpClient
from hueify.groups.lookup import GroupLookup, GroupInfo
from hueify.scenes.service import SceneService
from hueify.scenes.models import SceneInfo
from hueify.utils.logging import LoggingMixin


class GroupService(LoggingMixin):
    def __init__(
        self,
        client: HttpClient | None = None,
        group_lookup: GroupLookup | None = None,
        scene_service: SceneService | None = None,
    ) -> None:
        super().__init__()
        self._client = client or HttpClient()
        self._group_lookup = group_lookup or GroupLookup(client=self._client)
        self._scene_service = scene_service or SceneService(client=self._client)

    async def activate_scene_for_room(
        self, 
        room_name: str,
        scene_name: str
    ) -> None:
        room = await self._group_lookup.get_room_by_name(room_name)
        scene = await self._scene_service.find_scene_by_name_in_group(scene_name, group_id=room.id)

        await self._scene_service.activate_scene_by_id(scene.id)
        self.logger.info(f"Activated scene '{scene_name}' for room '{room_name}'")

    async def activate_scene_for_zone(
        self, 
        zone_name: str, 
        scene_name: str
    ) -> None:
        zone = await self._group_lookup.get_zone_by_name(zone_name)
        scene = await self._scene_service.find_scene_by_name_in_group(scene_name, group_id=zone.id)
        
        await self._scene_service.activate_scene_by_id(scene.id)
        self.logger.info(f"Activated scene '{scene_name}' for zone '{zone_name}'")

    async def get_scenes_for_room(self, room_name: str) -> list[SceneInfo]:
        room = await self._group_lookup.get_room_by_name(room_name)
        return await self._scene_service.get_scenes_by_group_id(room.id)

    async def get_scenes_for_zone(self, zone_name: str) -> list[SceneInfo]:
        zone = await self._group_lookup.get_zone_by_name(zone_name)
        return await self._scene_service.get_scenes_by_group_id(zone.id)

    async def get_active_scene_for_room(self, room_name: str) -> SceneInfo | None:
        scenes = await self.get_scenes_for_room(room_name)
        
        for scene in scenes:
            if scene.status and scene.status.active.value == "active":
                return scene
        
        return None

    async def get_active_scene_for_zone(self, zone_name: str) -> SceneInfo | None:
        scenes = await self.get_scenes_for_zone(zone_name)
        
        for scene in scenes:
            if scene.status and scene.status.active.value == "active":
                return scene
        
        return None

    async def get_all_rooms(self) -> list[GroupInfo]:
        return await self._group_lookup.get_rooms()

    async def get_all_zones(self) -> list[GroupInfo]:
        return await self._group_lookup.get_zones()
