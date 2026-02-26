import logging

from hueify.cache import PopulatableCache
from hueify.cache.lookup import EntityLookupCache
from hueify.grouped_lights.models import GroupedLightInfo
from hueify.http import HttpClient
from hueify.sse.bus import EventBus
from hueify.sse.views import GroupedLightEvent

logger = logging.getLogger(__name__)


class GroupedLightCache(EntityLookupCache[GroupedLightInfo], PopulatableCache):
    def __init__(self, event_bus: EventBus) -> None:
        super().__init__()
        event_bus.subscribe(GroupedLightEvent, self._on_grouped_light_event)
        logger.debug("GroupedLightCache subscribed to GroupedLightEvent")

    async def populate(self, http_client: HttpClient) -> None:
        grouped_lights = await http_client.get_resources(
            endpoint="/grouped_light", resource_type=GroupedLightInfo
        )
        await self.store_all(grouped_lights)

    async def _on_grouped_light_event(self, event: GroupedLightEvent) -> None:
        self.update_from_event(
            event.id,
            event.model_dump(exclude_none=True, exclude={"id", "type"}),
        )
        logger.debug(f"Updated grouped light {event.id} from SSE event")
