import logging

from hueify.cache import PopulatableCache
from hueify.cache.lookup import NamedEntityLookupCache
from hueify.grouped_lights.models import GroupInfo
from hueify.http import HttpClient

logger = logging.getLogger(__name__)


class RoomCache(NamedEntityLookupCache[GroupInfo], PopulatableCache):
    """Cache for room resources.

    Rooms don't emit SSE events themselves — their live state (on/off, brightness)
    is carried by the associated GroupedLightEvent, which is tracked in
    GroupedLightCache. This cache holds the static room metadata and service
    references populated at startup via REST.
    """

    def __init__(self) -> None:
        super().__init__()
        logger.debug("RoomCache initialised")

    async def populate(self, http_client: HttpClient) -> None:
        rooms = await http_client.get_resources(
            endpoint="/room", resource_type=GroupInfo
        )
        await self.store_all(rooms)
