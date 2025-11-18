from uuid import UUID

from hueify.lights.exceptions import LightNotFoundException
from hueify.lights.models import LightInfo
from hueify.shared.resource.lookup import NamedResourceLookup
from hueify.shared.resource.models import ResourceType


class LightLookup(NamedResourceLookup[LightInfo]):
    def get_resource_type(self) -> ResourceType:
        return ResourceType.LIGHT

    def get_model_type(self) -> type[LightInfo]:
        return LightInfo

    def _get_endpoint(self) -> str:
        return "light"

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
