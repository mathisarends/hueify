from urllib.parse import quote
from uuid import UUID

from pydantic import BaseModel, TypeAdapter

from hueify.http import HttpClient
from hueify.models import HueApiResponse, ResourceIdentifier

type ResourceId = str | UUID


class ResourceNamespace[TResource: BaseModel]:
    """Typed, stateless interface for one Hue CLIP v2 resource endpoint."""

    def __init__(
        self,
        resource_type: str,
        response_adapter: TypeAdapter[HueApiResponse[TResource]],
        http_client: HttpClient,
    ) -> None:
        self.resource_type = resource_type
        self._response_adapter = response_adapter
        self._http_client = http_client

    async def list(self) -> HueApiResponse[TResource]:
        return await self._http_client.get(self.resource_type, self._response_adapter)

    async def get(self, resource_id: ResourceId) -> HueApiResponse[TResource]:
        return await self._http_client.get(
            self._resource_path(resource_id), self._response_adapter
        )

    async def _create(self, data: BaseModel) -> HueApiResponse[ResourceIdentifier]:
        return await self._http_client.post(self.resource_type, data)

    async def _update(
        self, resource_id: ResourceId, data: BaseModel
    ) -> HueApiResponse[ResourceIdentifier]:
        return await self._http_client.put(self._resource_path(resource_id), data)

    async def _delete(
        self, resource_id: ResourceId
    ) -> HueApiResponse[ResourceIdentifier]:
        return await self._http_client.delete(self._resource_path(resource_id))

    def _resource_path(self, resource_id: ResourceId) -> str:
        return f"{self.resource_type}/{quote(str(resource_id), safe='')}"
