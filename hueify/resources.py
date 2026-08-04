from urllib.parse import quote
from uuid import UUID

from pydantic import BaseModel, TypeAdapter

from hueify.http import HttpClient
from hueify.models import (
    GroupUpdate,
    HueApiResponse,
    Light,
    LightUpdate,
    ResourceIdentifier,
    Room,
    Scene,
    SceneRecallRequest,
    SceneUpdate,
    Zone,
)

type ResourceId = str | UUID


class ResourceNamespace[TResource: BaseModel, TWrite: BaseModel]:
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

    async def get_all(self) -> HueApiResponse[TResource]:
        return await self._http_client.get(self.resource_type, self._response_adapter)

    async def get(self, resource_id: ResourceId) -> HueApiResponse[TResource]:
        return await self._http_client.get(
            self._resource_path(resource_id), self._response_adapter
        )

    async def create(self, data: TWrite) -> HueApiResponse[ResourceIdentifier]:
        return await self._http_client.post(self.resource_type, data)

    async def update(
        self, resource_id: ResourceId, data: TWrite
    ) -> HueApiResponse[ResourceIdentifier]:
        return await self._http_client.put(self._resource_path(resource_id), data)

    async def delete(
        self, resource_id: ResourceId
    ) -> HueApiResponse[ResourceIdentifier]:
        return await self._http_client.delete(self._resource_path(resource_id))

    def _resource_path(self, resource_id: ResourceId) -> str:
        return f"{self.resource_type}/{quote(str(resource_id), safe='')}"


class LightNamespace(ResourceNamespace[Light, LightUpdate]):
    def __init__(self, http_client: HttpClient) -> None:
        super().__init__("light", TypeAdapter(HueApiResponse[Light]), http_client)


class RoomNamespace(ResourceNamespace[Room, GroupUpdate]):
    def __init__(self, http_client: HttpClient) -> None:
        super().__init__("room", TypeAdapter(HueApiResponse[Room]), http_client)


class ZoneNamespace(ResourceNamespace[Zone, GroupUpdate]):
    def __init__(self, http_client: HttpClient) -> None:
        super().__init__("zone", TypeAdapter(HueApiResponse[Zone]), http_client)


class SceneNamespace(ResourceNamespace[Scene, SceneUpdate]):
    def __init__(self, http_client: HttpClient) -> None:
        super().__init__("scene", TypeAdapter(HueApiResponse[Scene]), http_client)

    async def recall(
        self,
        scene_id: ResourceId,
        request: SceneRecallRequest | None = None,
    ) -> HueApiResponse[ResourceIdentifier]:
        return await self._http_client.put(
            self._resource_path(scene_id), request or SceneRecallRequest()
        )
