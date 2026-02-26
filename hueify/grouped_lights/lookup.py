from uuid import UUID

from hueify.grouped_lights.models import GroupedLightInfo
from hueify.shared.resource.lookup import ResourceLookup


class GroupedLightLookup(ResourceLookup[GroupedLightInfo]):
    async def get_entity_by_id(self, entity_id: UUID) -> GroupedLightInfo | None:
        all_entities = await self.get_all_entities()
        return next((e for e in all_entities if e.id == entity_id), None)

    def get_model_type(self) -> type[GroupedLightInfo]:
        return GroupedLightInfo

    def _get_endpoint(self) -> str:
        return "grouped_light"
