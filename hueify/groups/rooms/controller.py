from hueify.groups.base import GroupController, GroupLookup
from hueify.groups.rooms.lookup import RoomLookup
from hueify.http.client import HttpClient


class RoomController(GroupController):
    @classmethod
    def _create_lookup(cls, client: HttpClient) -> GroupLookup:
        return RoomLookup(client=client)
