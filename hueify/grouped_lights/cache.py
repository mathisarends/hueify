import logging

from hueify.cache.lookup.base import EntityLookupCache
from hueify.grouped_lights.models import GroupedLightInfo
from hueify.sse.bus import EventBus
from hueify.sse.views import GroupedLightEvent

logger = logging.getLogger(__name__)


class GroupedLightCache(EntityLookupCache[GroupedLightInfo]):
    def __init__(self, event_bus: EventBus) -> None:
        super().__init__()
        event_bus.subscribe(GroupedLightEvent, self._on_grouped_light_event)
        logger.debug("GroupedLightCache subscribed to GroupedLightEvent")

    async def _on_grouped_light_event(self, event: GroupedLightEvent) -> None:
        self.update_from_event(
            event.id,
            event.model_dump(exclude_none=True, exclude={"id", "type"}),
        )
        logger.debug(f"Updated grouped light {event.id} from SSE event")
