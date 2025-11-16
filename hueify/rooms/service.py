from hueify.grouped_lights import Group
from hueify.http import HttpClient
from hueify.rooms.lookup import RoomLookup
from hueify.shared.resource.lookup import ResourceLookup


class Room(Group):
    @classmethod
    def _create_lookup(cls, client: HttpClient) -> ResourceLookup:
        return RoomLookup(client=client)
