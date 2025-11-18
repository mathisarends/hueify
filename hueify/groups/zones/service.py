from hueify.groups.service import Group
from hueify.groups.zones.lookup import ZoneLookup
from hueify.http.client import HttpClient
from hueify.shared.resource.lookup import NamedResourceLookup


class Zone(Group):
    @classmethod
    def _create_lookup(cls, client: HttpClient) -> NamedResourceLookup:
        return ZoneLookup(client=client)
