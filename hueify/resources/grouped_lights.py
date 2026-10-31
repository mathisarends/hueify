from urllib.parse import quote

from pydantic import TypeAdapter

from hueify.errors import ResourceNotFoundError
from hueify.http import HttpClient
from hueify.models import GroupedLight, HueApiResponse, LightUpdate, ResourceIdentifier
from hueify.resources.base import ResourceId
from hueify.resources.controls import LightCommands

_RESPONSE = TypeAdapter(HueApiResponse[GroupedLight])


class GroupedLightNamespace(LightCommands):
    """Commands for resolved grouped-light IDs, with no group lookup or state cache."""

    def __init__(self, http_client: HttpClient) -> None:
        self._http_client = http_client

    async def list(self) -> HueApiResponse[GroupedLight]:
        return await self._http_client.get("grouped_light", _RESPONSE)

    async def get(self, resource_id: ResourceId) -> HueApiResponse[GroupedLight]:
        return await self._http_client.get(self._path(resource_id), _RESPONSE)

    async def get_one(self, resource_id: ResourceId) -> GroupedLight:
        response = await self.get(resource_id)
        if not response.data:
            raise ResourceNotFoundError(f"No grouped light with ID {resource_id}")
        return response.data[0]

    async def apply(
        self, resource_id: ResourceId, update: LightUpdate
    ) -> HueApiResponse[ResourceIdentifier]:
        return await self._http_client.put(self._path(resource_id), update)

    async def is_on(self, resource_id: ResourceId) -> bool:
        return (await self.get_one(resource_id)).is_on is True

    @staticmethod
    def _path(resource_id: ResourceId) -> str:
        return f"grouped_light/{quote(str(resource_id), safe='')}"
