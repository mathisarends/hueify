from pydantic import TypeAdapter

from hueify.http import HttpClient
from hueify.models import HueApiResponse, Light, LightUpdate, ResourceIdentifier
from hueify.resources.base import ResourceId, ResourceNamespace
from hueify.resources.controls import LightCommands


class LightNamespace(LightCommands, ResourceNamespace[Light]):
    def __init__(self, http_client: HttpClient) -> None:
        super().__init__("light", TypeAdapter(HueApiResponse[Light]), http_client)

    async def update(
        self, light_id: ResourceId, data: LightUpdate
    ) -> HueApiResponse[ResourceIdentifier]:
        return await self._update(light_id, data)

    async def apply(
        self, light_id: ResourceId, update: LightUpdate
    ) -> HueApiResponse[ResourceIdentifier]:
        return await self._update(light_id, update)

    async def is_on(self, light_id: ResourceId) -> bool:
        return (await self.get_one(light_id)).on.on
