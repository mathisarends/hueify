from hueify.http import HttpClient
from hueify.models import GroupedLight, HueApiResponse, LightUpdate, ResourceIdentifier
from hueify.resources.base import ResourceId, UpdateNamespace
from hueify.resources.controls import LightCommands


class GroupedLightNamespace(LightCommands, UpdateNamespace[GroupedLight, LightUpdate]):
    """Direct control of a grouped_light service, without resolving a room."""

    def __init__(self, http_client: HttpClient) -> None:
        super().__init__("grouped_light", GroupedLight, LightUpdate, http_client)

    async def apply(
        self, resource_id: ResourceId, update: LightUpdate
    ) -> HueApiResponse[ResourceIdentifier]:
        return await self.update(resource_id, update)

    async def is_on(self, resource_id: ResourceId) -> bool:
        return (await self.get_one(resource_id)).is_on is True
