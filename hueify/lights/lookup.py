from uuid import UUID

from hueify.groups.base.lookup import ResourceLookup
from hueify.http import ApiResponse
from hueify.lights.exceptions import LightNotFoundException
from hueify.lights.models import LightInfo, LightInfoListAdapter
from hueify.shared.types import ResourceType


class LightLookup(ResourceLookup[LightInfo]):
    def get_resource_type(self) -> ResourceType:
        return ResourceType.LIGHT

    def _get_endpoint(self) -> str:
        return "light"

    def _extract_name(self, entity: LightInfo) -> str:
        return entity.metadata.name

    def _parse_response(self, response: ApiResponse) -> list[LightInfo]:
        data = response.get("data", [])
        if not data:
            return []
        return LightInfoListAdapter.validate_python(data)

    def _create_not_found_exception(
        self, lookup_name: str, suggested_names: list[str]
    ) -> Exception:
        return LightNotFoundException(
            light_name=lookup_name, suggestions=suggested_names
        )

    async def get_light_by_name(self, light_name: str) -> LightInfo:
        return await self.get_entity_by_name(light_name)

    async def get_light_by_id(self, light_id: UUID) -> LightInfo:
        lights = await self.get_all_entities()

        for light in lights:
            if light.id == light_id:
                return light

        raise LightNotFoundException(light_name=str(light_id), suggestions=[])

    async def get_lights(self) -> list[LightInfo]:
        return await self.get_all_entities()

    async def get_light_names(self) -> list[str]:
        lights = await self.get_lights()
        return [light.metadata.name for light in lights]
