import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

from pydantic import BaseModel

from hueify.shared.types import ResourceType
from hueify.utils.logging import LoggingMixin

T = TypeVar("T", bound=BaseModel)
Fetcher = Callable[[], Awaitable[list[T]]]


class LookupCache(LoggingMixin):
    def __init__(self) -> None:
        self._cache: dict[ResourceType, list[BaseModel]] = {}
        self._lock = asyncio.Lock()

    async def get_or_fetch(
        self,
        entity_type: ResourceType,
        all_entities_fetcher: Fetcher[T],
    ) -> list[T]:
        cached = self._cache.get(entity_type)
        if cached is not None:
            self.logger.debug(f"Cache HIT for {entity_type}")
            return cached

        async with self._lock:
            cached = self._cache.get(entity_type)
            if cached is not None:
                self.logger.debug(f"Cache HIT (after lock) for {entity_type}")
                return cached

            self.logger.debug(f"Cache MISS for {entity_type}. Fetching...")
            fresh = await all_entities_fetcher()
            self._cache[entity_type] = fresh
            self.logger.info(f"Cached {entity_type}")
            return fresh

    async def clear_all(self) -> None:
        async with self._lock:
            self._cache.clear()
            self.logger.info("Cache cleared")

    async def clear_by_type(self, resource_type: ResourceType) -> None:
        async with self._lock:
            if resource_type in self._cache:
                del self._cache[resource_type]
                self.logger.info(f"Cache cleared for {resource_type}")


_cache_instance: LookupCache | None = None


def get_cache() -> LookupCache:
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = LookupCache()
    return _cache_instance
