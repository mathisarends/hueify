from hueify.grouped_lights.service import Group
from hueify.http.client import HttpClient
from hueify.shared.resource.lookup import ResourceLookup
from hueify.zones.lookup import ZoneLookup


class Zone(Group):
    @classmethod
    def _create_lookup(cls, client: HttpClient) -> ResourceLookup:
        return ZoneLookup(client=client)
