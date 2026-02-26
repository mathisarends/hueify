import logging
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

logger = logging.getLogger(__name__)


class EntityLookupCache(Generic[T]):
    def __init__(self) -> None:
        self._id_to_model: dict[UUID, T] = {}

    def get_all(self) -> list[T]:
        return list(self._id_to_model.values())

    def get_by_id(self, entity_id: UUID) -> T | None:
        return self._id_to_model.get(entity_id)

    def store_all(self, entities: list[T]) -> None:
        self._id_to_model.clear()
        for entity in entities:
            self._store_single(entity)

    def _store_single(self, entity: T) -> None:
        self._id_to_model[entity.id] = entity

    def update_from_event(self, resource_id: UUID, event_data: dict) -> None:
        cached_resource = self._id_to_model.get(resource_id)
        if cached_resource is None:
            return

        try:
            merged = {**cached_resource.model_dump(), **event_data}
            updated_resource = cached_resource.model_validate(merged)
            self._id_to_model[resource_id] = updated_resource
            logger.debug(f"Updated cached resource with ID {resource_id}")
        except Exception as e:
            logger.error(
                f"Failed to update cached resource {resource_id}: {e}",
                exc_info=True,
            )

    def clear(self) -> None:
        self._id_to_model.clear()


class NamedEntityLookupCache(EntityLookupCache[T]):
    def __init__(self) -> None:
        super().__init__()
        self._name_to_model: dict[str, T] = {}

    def get_by_name(self, name: str) -> T | None:
        return self._name_to_model.get(name.lower())

    def _store_single(self, entity: T) -> None:
        super()._store_single(entity)

        entity_name = entity.metadata.name.lower()
        existing = self._name_to_model.get(entity_name)

        if existing is not None and existing.id != entity.id:
            logger.warning(
                f"Name collision for '{entity_name}': IDs {existing.id} and {entity.id}"
            )

        self._name_to_model[entity_name] = entity

    def update_from_event(self, resource_id: UUID, event_data: dict) -> None:
        super().update_from_event(resource_id, event_data)

        cached_resource = self._id_to_model.get(resource_id)
        if cached_resource is not None:
            entity_name = cached_resource.metadata.name.lower()
            self._name_to_model[entity_name] = cached_resource

    def clear(self) -> None:
        super().clear()
        self._name_to_model.clear()
