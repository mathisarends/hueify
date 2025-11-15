from hueify.groups.base import Group, ResourceLookup
from hueify.groups.zones.lookup import ZoneLookup
from hueify.http.client import HttpClient


class Zone(Group):
    @classmethod
    def _create_lookup(cls, client: HttpClient) -> ResourceLookup:
        return ZoneLookup(client=client)
