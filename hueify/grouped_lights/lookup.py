from typing import override
from uuid import UUID

from hueify.grouped_lights.models import GroupedLightInfo
from hueify.shared.resource.lookup import ResourceLookup
from hueify.shared.resource.models import ResourceType


class GroupedLightLookup(ResourceLookup[GroupedLightInfo]):
    async def get_entity_by_id(self, entity_id: UUID) -> GroupedLightInfo | None:
        resource_type = self.get_resource_type()

        cached = self._cache.get_by_id(resource_type, entity_id)
        if cached:
            return cached

        await self.get_all_entities()

        return self._cache.get_by_id(resource_type, entity_id)

    @override
    def get_resource_type(self) -> ResourceType:
        return ResourceType.GROUPED_LIGHT

    @override
    def get_model_type(self) -> type[GroupedLightInfo]:
        return GroupedLightInfo

    @override
    def _get_endpoint(self) -> str:
        return "grouped_light"
