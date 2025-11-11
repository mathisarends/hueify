import asyncio
from hueify.groups.models import GroupInfo
from hueify.groups.rooms.lookup import RoomLookup
from hueify.groups.zones.lookup import ZoneLookup

class GroupDiscovery:
    def __init__(self, room_lookup: RoomLookup | None = None, zone_lookup: ZoneLookup | None = None) -> None:
        self._room_lookup = room_lookup or RoomLookup()
        self._zone_lookup = zone_lookup or ZoneLookup()

    async def get_all_groups(self) -> list[GroupInfo]:
        rooms_task = self.get_all_rooms()
        zones_task = self.get_all_zones()
        rooms, zones = await asyncio.gather(rooms_task, zones_task)
        return rooms + zones

    async def get_all_rooms(self) -> list[GroupInfo]:
        return await self._room_lookup._get_all_groups()

    async def get_all_zones(self) -> list[GroupInfo]:
        return await self._zone_lookup._get_all_groups()
