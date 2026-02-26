import logging

from hueify.cache.lookup.base import NamedEntityLookupCache
from hueify.scenes.models import SceneInfo
from hueify.sse.bus import EventBus
from hueify.sse.views import SceneEvent

logger = logging.getLogger(__name__)


class SceneCache(NamedEntityLookupCache[SceneInfo]):
    def __init__(self, event_bus: EventBus) -> None:
        super().__init__()
        event_bus.subscribe(SceneEvent, self._on_scene_event)
        logger.debug("SceneCache subscribed to SceneEvent")

    async def _on_scene_event(self, event: SceneEvent) -> None:
        self.update_from_event(
            event.id,
            event.model_dump(exclude_none=True, exclude={"id", "type"}),
        )
        logger.debug(f"Updated scene {event.id} from SSE event")
