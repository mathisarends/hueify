import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import TypeVar
from uuid import UUID

from hueify.cache.lookup.base import EntityLookupCache, NamedEntityLookupCache
from hueify.events import EventBus
from hueify.grouped_lights import GroupedLightLookup
from hueify.groups.rooms import RoomLookup
from hueify.groups.zones import ZoneLookup
from hueify.lights.lookup import LightLookup
from hueify.scenes.lookup import SceneLookup
from hueify.shared.resource.models import ResourceInfo, ResourceType
from hueify.sse.models import GroupedLightEvent, LightEvent, SceneEvent

T = TypeVar("T", bound=ResourceInfo)
Fetcher = Callable[[], Awaitable[list[T]]]

logger = logging.getLogger(__name__)


class LookupCache:
    def __init__(self, event_bus: EventBus) -> None:
        self._cache_map: dict[ResourceType, EntityLookupCache] = {
            ResourceType.LIGHT: NamedEntityLookupCache(),
            ResourceType.SCENE: NamedEntityLookupCache(),
            ResourceType.ROOM: NamedEntityLookupCache(),
            ResourceType.ZONE: NamedEntityLookupCache(),
            ResourceType.GROUPED_LIGHT: EntityLookupCache(),
        }

        self._subscribe_to_events(event_bus)

    def _subscribe_to_events(self, event_bus: EventBus) -> None:
        event_bus.subscribe_to_light(self._handle_light_event)
        event_bus.subscribe_to_grouped_light(self._handle_grouped_light_event)
        event_bus.subscribe_to_scene(self._handle_scene_event)
        logger.info("Cache subscribed to event bus")

    async def populate(self) -> None:
        light_lookup = LightLookup()
        room_lookup = RoomLookup()
        zone_lookup = ZoneLookup()
        scene_lookup = SceneLookup()
        grouped_light_lookup = GroupedLightLookup()

        await asyncio.gather(
            light_lookup.get_lights(),
            room_lookup.get_all_entities(),
            zone_lookup.get_all_entities(),
            scene_lookup.get_scenes(),
            grouped_light_lookup.get_all_entities(),
        )
        logger.info("Cache warmed up successfully")

    async def get_or_fetch(
        self,
        entity_type: ResourceType,
        all_entities_fetcher: Fetcher[T],
    ) -> list[T]:
        cache = self._get_cache_for_type(entity_type)
        cached_models = cache.get_all()

        if cached_models:
            logger.debug(f"Cache HIT for {entity_type}")
            return cached_models

        logger.debug(f"Cache MISS for {entity_type}. Fetching...")
        fresh = await all_entities_fetcher()
        await cache.store_all(fresh)
        logger.info(f"Cached {len(fresh)} entities for {entity_type}")
        return fresh

    def _get_cache_for_type(self, resource_type: ResourceType) -> EntityLookupCache:
        cache = self._cache_map.get(resource_type)
        if cache is None:
            raise ValueError(f"Unsupported resource type: {resource_type}")
        return cache

    def get_by_name(self, entity_type: ResourceType, name: str) -> ResourceInfo | None:
        cache = self._get_cache_for_type(entity_type)
        if not isinstance(cache, NamedEntityLookupCache):
            raise ValueError(f"{entity_type} does not support name-based lookup")
        return cache.get_by_name(name)

    def get_by_id(
        self, entity_type: ResourceType, entity_id: UUID
    ) -> ResourceInfo | None:
        cache = self._get_cache_for_type(entity_type)
        return cache.get_by_id(entity_id)

    async def clear_all(self) -> None:
        await asyncio.gather(*[cache.clear() for cache in self._cache_map.values()])
        logger.info("All caches cleared")

    async def clear_by_type(self, resource_type: ResourceType) -> None:
        cache = self._get_cache_for_type(resource_type)
        await cache.clear()
        logger.info(f"Cache cleared for {resource_type}")

    def _handle_light_event(self, event: LightEvent) -> None:
        cache = self._cache_map[ResourceType.LIGHT]
        cache.update_from_event(
            event.id, event.model_dump(exclude_unset=True, exclude_none=True)
        )

    def _handle_grouped_light_event(self, event: GroupedLightEvent) -> None:
        cache = self._cache_map[ResourceType.GROUPED_LIGHT]
        cache.update_from_event(
            event.id, event.model_dump(exclude_unset=True, exclude_none=True)
        )

    def _handle_scene_event(self, event: SceneEvent) -> None:
        cache = self._cache_map[ResourceType.SCENE]
        cache.update_from_event(
            event.id, event.model_dump(exclude_unset=True, exclude_none=True)
        )
