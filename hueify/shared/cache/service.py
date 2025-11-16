import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar
from uuid import UUID

from hueify.groups.rooms.lookup import RoomLookup
from hueify.groups.zones.lookup import ZoneLookup
from hueify.lights.lookup import LightLookup
from hueify.scenes.lookup import SceneLookup
from hueify.shared.cache.lookup import (
    BaseCache,
    GroupedLightsCache,
    LightCache,
    RoomCache,
    SceneCache,
    ZoneCache,
)
from hueify.shared.resource.models import ResourceInfo, ResourceType
from hueify.sse import get_event_bus
from hueify.sse.models import GroupedLightEvent, LightEvent, SceneEvent
from hueify.utils.logging import LoggingMixin

T = TypeVar("T", bound=ResourceInfo)
Fetcher = Callable[[], Awaitable[list[T]]]


class LookupCache(LoggingMixin):
    def __init__(self) -> None:
        self._light_cache = LightCache()
        self._scene_cache = SceneCache()
        self._room_cache = RoomCache()
        self._zone_cache = ZoneCache()
        self._grouped_lights_cache = GroupedLightsCache()

        self._cache_map = {
            ResourceType.LIGHT: self._light_cache,
            ResourceType.SCENE: self._scene_cache,
            ResourceType.ROOM: self._room_cache,
            ResourceType.ZONE: self._zone_cache,
            ResourceType.GROUPED_LIGHT: self._grouped_lights_cache,
        }
        self._event_subscription_initialized = False

    async def warm_up(self) -> None:
        light_lookup = LightLookup()
        room_lookup = RoomLookup()
        zone_lookup = ZoneLookup()
        scene_lookup = SceneLookup()

        await asyncio.gather(
            light_lookup.get_lights(),
            room_lookup.get_all_entities(),
            zone_lookup.get_all_entities(),
            scene_lookup.get_scenes(),
        )
        self.logger.info("Cache warmed up successfully")

    async def get_or_fetch(
        self,
        entity_type: ResourceType,
        all_entities_fetcher: Fetcher[T],
    ) -> list[T]:
        await self._ensure_event_subscription()

        cache = self._get_cache_for_type(entity_type)
        cached_models = cache.get_all()

        if cached_models:
            self.logger.debug(f"Cache HIT for {entity_type}")
            return cached_models

        self.logger.debug(f"Cache MISS for {entity_type}. Fetching...")
        fresh = await all_entities_fetcher()
        await cache.store_all(fresh)
        self.logger.info(f"Cached {len(fresh)} entities for {entity_type}")
        return fresh

    def _get_cache_for_type(self, resource_type: ResourceType) -> BaseCache:
        cache = self._cache_map.get(resource_type)
        if cache is None:
            raise ValueError(f"Unsupported resource type: {resource_type}")
        return cache

    def get_by_name(self, entity_type: ResourceType, name: str) -> ResourceInfo | None:
        cache = self._get_cache_for_type(entity_type)
        return cache.get_by_name(name)

    def get_by_id(
        self, entity_type: ResourceType, entity_id: UUID
    ) -> ResourceInfo | None:
        cache = self._get_cache_for_type(entity_type)
        return cache.get_by_id(entity_id)

    async def clear_all(self) -> None:
        await asyncio.gather(
            self._light_cache.clear(),
            self._scene_cache.clear(),
            self._room_cache.clear(),
            self._zone_cache.clear(),
            self._grouped_lights_cache.clear(),
        )
        self.logger.info("All caches cleared")

    async def clear_by_type(self, resource_type: ResourceType) -> None:
        cache = self._get_cache_for_type(resource_type)
        await cache.clear()
        self.logger.info(f"Cache cleared for {resource_type}")

    async def _ensure_event_subscription(self) -> None:
        if self._event_subscription_initialized:
            return

        try:
            event_bus = await get_event_bus()

            event_bus.subscribe_to_light(self._handle_light_event)
            event_bus.subscribe_to_grouped_light(self._handle_grouped_light_event)
            event_bus.subscribe_to_scene(self._handle_scene_event)

            self._event_subscription_initialized = True
            self.logger.info("Event subscriptions initialized for cache updates")
        except Exception as e:
            self.logger.warning(
                f"Failed to initialize event subscriptions: {e}", exc_info=True
            )

    def _handle_light_event(self, event: LightEvent) -> None:
        event_data = event.model_dump(exclude_unset=True, exclude_none=True)
        self._light_cache.update_from_event(event.id, event_data)

    def _handle_grouped_light_event(self, event: GroupedLightEvent) -> None:
        event_data = event.model_dump(exclude_unset=True, exclude_none=True)
        self._grouped_lights_cache.update_from_event(event.id, event_data)

    def _handle_scene_event(self, event: SceneEvent) -> None:
        event_data = event.model_dump(exclude_unset=True, exclude_none=True)
        self._scene_cache.update_from_event(event.id, event_data)


_cache_instance: LookupCache | None = None


def get_cache() -> LookupCache:
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = LookupCache()
    return _cache_instance
