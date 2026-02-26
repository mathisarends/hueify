import logging

from hueify.cache.lookup.base import NamedEntityLookupCache
from hueify.groups.models import GroupInfo
from hueify.sse.bus import EventBus

logger = logging.getLogger(__name__)


class ZoneCache(NamedEntityLookupCache[GroupInfo]):
    """Cache for zone resources.

    Zones don't emit SSE events themselves — their live state is tracked via
    the associated GroupedLightEvent in GroupedLightCache. This cache holds
    the static zone metadata and service references populated at startup via REST.
    """

    def __init__(self, event_bus: EventBus) -> None:
        super().__init__()
        logger.debug("ZoneCache initialised")
