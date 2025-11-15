from hueify.groups.base import Group, ResourceLookup
from hueify.groups.rooms.lookup import RoomLookup
from hueify.http.client import HttpClient


class Room(Group):
    @classmethod
    def _create_lookup(cls, client: HttpClient) -> ResourceLookup:
        return RoomLookup(client=client)
