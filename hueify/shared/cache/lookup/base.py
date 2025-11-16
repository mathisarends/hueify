from __future__ import annotations

import asyncio
from typing import Generic, TypeVar
from uuid import UUID

from hueify.shared.resource.models import ResourceInfo
from hueify.utils.logging import LoggingMixin

T = TypeVar("T", bound=ResourceInfo)


class BaseCache(LoggingMixin, Generic[T]):
    def __init__(self) -> None:
        self._name_to_model: dict[str, T] = {}
        self._id_to_model: dict[UUID, T] = {}
        self._lock = asyncio.Lock()

    async def get_all(self) -> list[T]:
        return list(self._id_to_model.values())

    def get_by_name(self, name: str) -> T | None:
        return self._name_to_model.get(name.lower())

    def get_by_id(self, entity_id: UUID) -> T | None:
        return self._id_to_model.get(entity_id)

    async def store_all(self, entities: list[T]) -> None:
        async with self._lock:
            self._id_to_model.clear()
            self._name_to_model.clear()

            for entity in entities:
                self._store_single(entity)

    def _store_single(self, entity: T) -> None:
        entity_id = entity.id
        entity_name = entity.metadata.name.lower()

        self._id_to_model[entity_id] = entity

        existing = self._name_to_model.get(entity_name)
        if existing is not None and existing.id != entity_id:
            self.logger.warning(
                f"Name collision for '{entity_name}': IDs {existing.id} and {entity_id}"
            )

        self._name_to_model[entity_name] = entity

    def update_from_event(self, resource_id: UUID, event_data: dict) -> None:
        cached_resource = self._id_to_model.get(resource_id)

        if cached_resource is None:
            return

        try:
            updated_resource = cached_resource.model_copy(update=event_data, deep=True)

            self._id_to_model[resource_id] = updated_resource

            entity_name = cached_resource.metadata.name.lower()
            self._name_to_model[entity_name] = updated_resource

            self.logger.debug(f"Updated cached resource with ID {resource_id}")
        except Exception as e:
            self.logger.error(
                f"Failed to update cached resource {resource_id}: {e}",
                exc_info=True,
            )

    async def clear(self) -> None:
        async with self._lock:
            self._name_to_model.clear()
            self._id_to_model.clear()
