import logging

from hueify.cache import PopulatableCache
from hueify.cache.lookup import NamedEntityLookupCache
from hueify.http import HttpClient
from hueify.scenes.schemas import SceneInfo
from hueify.sse.bus import EventBus
from hueify.sse.views import SceneEvent

logger = logging.getLogger(__name__)


class SceneCache(NamedEntityLookupCache[SceneInfo], PopulatableCache):
    def __init__(self, event_bus: EventBus) -> None:
        super().__init__()
        event_bus.subscribe(SceneEvent, self._on_scene_event)
        logger.debug("SceneCache subscribed to SceneEvent")

    async def populate(self, http_client: HttpClient) -> None:
        scenes = await http_client.get_resources(
            endpoint="/scene", resource_type=SceneInfo
        )
        await self.store_all(scenes)

    async def _on_scene_event(self, event: SceneEvent) -> None:
        self.update_from_event(
            event.id,
            event.model_dump(exclude_none=True, exclude={"id", "type"}),
        )
        logger.debug(f"Updated scene {event.id} from SSE event")
