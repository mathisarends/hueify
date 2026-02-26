import logging

from hueify.groups.models import GroupInfo
from hueify.shared.lookup import NamedEntityLookupCache

logger = logging.getLogger(__name__)


class ZoneCache(NamedEntityLookupCache[GroupInfo]):
    """Cache for zone resources.

    Zones don't emit SSE events themselves — their live state is tracked via
    the associated GroupedLightEvent in GroupedLightCache. This cache holds
    the static zone metadata and service references populated at startup via REST.
    """

    def __init__(self) -> None:
        super().__init__()
        logger.debug("ZoneCache initialised")
