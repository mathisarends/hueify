import logging

from hueify.cache import ManagedCache
from hueify.cache.lookup import NamedEntityLookupCache
from hueify.grouped_lights.views import GroupInfo
from hueify.http import HttpClient

logger = logging.getLogger(__name__)


class ZoneCache(NamedEntityLookupCache[GroupInfo], ManagedCache):
    def __init__(self) -> None:
        super().__init__()
        logger.debug("ZoneCache initialised")

    async def populate(self, http_client: HttpClient) -> None:
        zones = await http_client.get_resources(
            endpoint="/zone", resource_type=GroupInfo
        )
        self.store_all(zones)
