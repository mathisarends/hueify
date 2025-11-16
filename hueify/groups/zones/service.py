from hueify.groups.service import Group
from hueify.groups.zones.lookup import ZoneLookup
from hueify.http.client import HttpClient
from hueify.shared.resource.lookup import ResourceLookup


class Zone(Group):
    @classmethod
    def _create_lookup(cls, client: HttpClient) -> ResourceLookup:
        return ZoneLookup(client=client)
