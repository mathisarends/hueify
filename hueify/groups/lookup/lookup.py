from hueify.http import HttpClient, ApiResponse
from hueify.groups.lookup.models import GroupInfo, GroupInfoListAdapter, GroupType
from hueify.groups.lookup.exceptions import GroupNotFoundError
from hueify.utils.fuzzy import find_all_matches


class GroupLookup:
    def __init__(self, client: HttpClient | None = None) -> None:
        self._client = client or HttpClient()

    async def get_room_by_name(self, room_name: str) -> GroupInfo:
        rooms = await self.get_rooms()
        
        for room in rooms:
            if room.name.lower() == room_name.lower():
                return room
        
        suggestions = find_all_matches(
            query=room_name,
            items=rooms,
            text_extractor=lambda r: r.name,
            min_similarity=0.6
        )
        
        raise GroupNotFoundError(
            group_type=GroupType.ROOM,
            lookup_name=room_name,
            suggested_names=[s.name for s in suggestions]
        )

    async def get_zone_by_name(self, zone_name: str) -> GroupInfo:
        zones = await self.get_zones()
        
        for zone in zones:
            if zone.name.lower() == zone_name.lower():
                return zone
        
        suggestions = find_all_matches(
            query=zone_name,
            items=zones,
            text_extractor=lambda z: z.name,
            min_similarity=0.6
        )
        
        raise GroupNotFoundError(
            group_type=GroupType.ZONE,
            lookup_name=zone_name,
            suggested_names=[s.name for s in suggestions]
        )

    async def get_rooms(self) -> list[GroupInfo]:
        response = await self._client.get("room")
        return self._parse_groups_response(response)

    async def get_zones(self) -> list[GroupInfo]:
        response = await self._client.get("zone")
        return self._parse_groups_response(response)
    
    def _parse_groups_response(self, response: ApiResponse) -> list[GroupInfo]:
        data = response.get("data", [])
        if not data:
            return []
        
        return GroupInfoListAdapter.validate_python(data)