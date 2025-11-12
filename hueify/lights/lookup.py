from uuid import UUID

from hueify.http import HttpClient
from hueify.lights.exceptions import LightNotFoundException
from hueify.lights.models import LightInfo, LightInfoListAdapter
from hueify.utils.fuzzy import find_all_matches


class LightLookup:
    def __init__(self, client: HttpClient | None = None) -> None:
        self._client = client or HttpClient()

    async def get_light_by_name(self, light_name: str) -> LightInfo:
        lights = await self.get_lights()

        for light in lights:
            if light.metadata.name.lower() == light_name.lower():
                return light

        matching_lights = find_all_matches(
            query=light_name,
            items=lights,
            text_extractor=lambda light: light.metadata.name,
            min_similarity=0.6,
        )

        suggestions = [light.metadata.name for light in matching_lights]

        raise LightNotFoundException(light_name=light_name, suggestions=suggestions)

    async def get_light_by_id(self, light_id: UUID) -> LightInfo:
        lights = await self.get_lights()

        for light in lights:
            if light.id == light_id:
                return light

        raise LightNotFoundException(light_name=str(light_id), suggestions=[])

    async def get_lights(self) -> list[LightInfo]:
        response = await self._client.get("light")
        data = response.get("data", [])
        return LightInfoListAdapter.validate_python(data)

    async def get_light_names(self) -> list[str]:
        lights = await self.get_lights()
        return [light.metadata.name for light in lights]
