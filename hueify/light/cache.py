import logging

from hueify.cache import PopulatableCache
from hueify.cache.lookup import NamedEntityLookupCache
from hueify.http import HttpClient
from hueify.light.models import LightInfo
from hueify.sse.bus import EventBus
from hueify.sse.views import LightEvent

logger = logging.getLogger(__name__)


class LightCache(NamedEntityLookupCache[LightInfo], PopulatableCache):
    def __init__(self, event_bus: EventBus) -> None:
        super().__init__()
        event_bus.subscribe(LightEvent, self._on_light_event)
        logger.debug("LightCache subscribed to LightEvent")

    async def populate(self, http_client: HttpClient) -> None:
        lights = await http_client.get_resources(
            endpoint="/light", resource_type=LightInfo
        )
        await self.store_all(lights)

    async def _on_light_event(self, event: LightEvent) -> None:
        self.update_from_event(
            event.id,
            event.model_dump(exclude_none=True, exclude={"id", "type"}),
        )
        logger.debug(f"Updated light {event.id} from SSE event")
