from hueify.groups.base import GroupController, GroupLookup
from hueify.groups.zones.lookup import ZoneLookup
from hueify.http.client import HttpClient


class ZoneController(GroupController):
    @classmethod
    def _create_lookup(cls, client: HttpClient) -> GroupLookup:
        return ZoneLookup(client=client)
