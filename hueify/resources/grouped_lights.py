from pydantic import TypeAdapter

from hueify.http import HttpClient
from hueify.models import GroupedLight, HueApiResponse, LightUpdate, ResourceIdentifier
from hueify.resources.base import ResourceId, ResourceNamespace
from hueify.resources.controls import LightCommands


class GroupedLightNamespace(LightCommands, ResourceNamespace[GroupedLight]):
    """Direct control of a grouped_light service, without resolving a room."""

    def __init__(self, http_client: HttpClient) -> None:
        super().__init__(
            "grouped_light", TypeAdapter(HueApiResponse[GroupedLight]), http_client
        )

    async def update(
        self, resource_id: ResourceId, data: LightUpdate
    ) -> HueApiResponse[ResourceIdentifier]:
        return await self._update(resource_id, data)

    async def apply(
        self, resource_id: ResourceId, update: LightUpdate
    ) -> HueApiResponse[ResourceIdentifier]:
        return await self.update(resource_id, update)

    async def is_on(self, resource_id: ResourceId) -> bool:
        return (await self.get_one(resource_id)).is_on is True
