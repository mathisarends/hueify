import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar
from uuid import UUID

from hueify.shared.types import ResourceInfo, ResourceType
from hueify.utils.logging import LoggingMixin

T = TypeVar("T", bound=ResourceInfo)
Fetcher = Callable[[], Awaitable[list[T]]]


class LookupCache(LoggingMixin):
    def __init__(self) -> None:
        self._name_to_model: dict[str, ResourceInfo] = {}
        self._id_to_model: dict[str, ResourceInfo] = {}
        self._lock = asyncio.Lock()

    async def get_or_fetch(
        self,
        entity_type: ResourceType,
        all_entities_fetcher: Fetcher[T],
    ) -> list[T]:
        type_prefix = self._get_type_prefix(entity_type)

        cached_models = [
            model
            for key, model in self._id_to_model.items()
            if key.startswith(type_prefix)
        ]

        if cached_models:
            self.logger.debug(f"Cache HIT for {entity_type}")
            return cached_models

        async with self._lock:
            cached_models = [
                model
                for key, model in self._id_to_model.items()
                if key.startswith(type_prefix)
            ]

            if cached_models:
                self.logger.debug(f"Cache HIT (after lock) for {entity_type}")
                return cached_models

            self.logger.debug(f"Cache MISS for {entity_type}. Fetching...")
            fresh = await all_entities_fetcher()
            self._store_entities(fresh, entity_type)
            self.logger.info(f"Cached {len(fresh)} entities for {entity_type}")
            return fresh

    def _store_entities(
        self,
        entities: list[T],
        entity_type: ResourceType,
    ) -> None:
        type_prefix = self._get_type_prefix(entity_type)

        for entity in entities:
            entity_id = entity.id
            entity_name = entity.metadata.name

            id_key = f"{type_prefix}:{entity_id}"
            name_key = f"{type_prefix}:{entity_name.lower()}"

            self._id_to_model[id_key] = entity
            self._check_and_store_by_name(
                name_key, entity, entity_id, entity_name, entity_type
            )

    def _check_and_store_by_name(
        self,
        name_key: str,
        entity: T,
        entity_id: UUID,
        entity_name: str,
        entity_type: ResourceType,
    ) -> None:
        existing = self._name_to_model.get(name_key)

        if existing is None:
            self._name_to_model[name_key] = entity
            return

        existing_id = existing.id

        if existing_id == entity_id:
            self._name_to_model[name_key] = entity
            return

        self.logger.warning(
            f"Name collision for '{entity_name}' in {entity_type}: "
            f"IDs {existing_id} and {entity_id}"
        )
        self._name_to_model[name_key] = entity

    def get_by_name(self, entity_type: ResourceType, name: str) -> ResourceInfo | None:
        type_prefix = self._get_type_prefix(entity_type)
        name_key = f"{type_prefix}:{name.lower()}"
        return self._name_to_model.get(name_key)

    def get_by_id(
        self, entity_type: ResourceType, entity_id: UUID
    ) -> ResourceInfo | None:
        type_prefix = self._get_type_prefix(entity_type)
        id_key = f"{type_prefix}:{entity_id}"
        return self._id_to_model.get(id_key)

    async def clear_all(self) -> None:
        async with self._lock:
            self._name_to_model.clear()
            self._id_to_model.clear()
            self.logger.info("Cache cleared")

    async def clear_by_type(self, resource_type: ResourceType) -> None:
        async with self._lock:
            type_prefix = self._get_type_prefix(resource_type)

            name_keys_to_remove = [
                key for key in self._name_to_model if key.startswith(type_prefix)
            ]
            id_keys_to_remove = [
                key for key in self._id_to_model if key.startswith(type_prefix)
            ]

            for key in name_keys_to_remove:
                del self._name_to_model[key]
            for key in id_keys_to_remove:
                del self._id_to_model[key]

            self.logger.info(f"Cache cleared for {resource_type}")

    def _get_type_prefix(self, resource_type: ResourceType) -> str:
        return resource_type.value


_cache_instance: LookupCache | None = None


def get_cache() -> LookupCache:
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = LookupCache()
    return _cache_instance
