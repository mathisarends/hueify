import logging

from hueify.cache.lookup.base import NamedEntityLookupCache
from hueify.groups.models import GroupInfo
from hueify.sse.bus import EventBus

logger = logging.getLogger(__name__)


class RoomCache(NamedEntityLookupCache[GroupInfo]):
    """Cache for room resources.

    Rooms don't emit SSE events themselves — their live state (on/off, brightness)
    is carried by the associated GroupedLightEvent, which is tracked in
    GroupedLightCache. This cache holds the static room metadata and service
    references populated at startup via REST.
    """

    def __init__(self, event_bus: EventBus) -> None:
        super().__init__()
        logger.debug("RoomCache initialised")
