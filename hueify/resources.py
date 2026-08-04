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

    async def get_all(self) -> HueApiResponse[TResource]:
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


class LightNamespace(ResourceNamespace[Light]):
    def __init__(self, http_client: HttpClient) -> None:
        super().__init__("light", TypeAdapter(HueApiResponse[Light]), http_client)

    async def update(
        self, light_id: ResourceId, data: LightUpdate
    ) -> HueApiResponse[ResourceIdentifier]:
        return await self._update(light_id, data)


class RoomNamespace(ResourceNamespace[Room]):
    def __init__(self, http_client: HttpClient) -> None:
        super().__init__("room", TypeAdapter(HueApiResponse[Room]), http_client)

    async def create(self, data: GroupUpdate) -> HueApiResponse[ResourceIdentifier]:
        return await self._create(data)

    async def update(
        self, room_id: ResourceId, data: GroupUpdate
    ) -> HueApiResponse[ResourceIdentifier]:
        return await self._update(room_id, data)

    async def delete(self, room_id: ResourceId) -> HueApiResponse[ResourceIdentifier]:
        return await self._delete(room_id)


class ZoneNamespace(ResourceNamespace[Zone]):
    def __init__(self, http_client: HttpClient) -> None:
        super().__init__("zone", TypeAdapter(HueApiResponse[Zone]), http_client)

    async def create(self, data: GroupUpdate) -> HueApiResponse[ResourceIdentifier]:
        return await self._create(data)

    async def update(
        self, zone_id: ResourceId, data: GroupUpdate
    ) -> HueApiResponse[ResourceIdentifier]:
        return await self._update(zone_id, data)

    async def delete(self, zone_id: ResourceId) -> HueApiResponse[ResourceIdentifier]:
        return await self._delete(zone_id)


class SceneNamespace(ResourceNamespace[Scene]):
    def __init__(self, http_client: HttpClient) -> None:
        super().__init__("scene", TypeAdapter(HueApiResponse[Scene]), http_client)

    async def create(self, data: SceneUpdate) -> HueApiResponse[ResourceIdentifier]:
        return await self._create(data)

    async def update(
        self, scene_id: ResourceId, data: SceneUpdate
    ) -> HueApiResponse[ResourceIdentifier]:
        return await self._update(scene_id, data)

    async def delete(self, scene_id: ResourceId) -> HueApiResponse[ResourceIdentifier]:
        return await self._delete(scene_id)

    async def recall(
        self,
        scene_id: ResourceId,
        request: SceneRecallRequest | None = None,
    ) -> HueApiResponse[ResourceIdentifier]:
        return await self._http_client.put(
            self._resource_path(scene_id), request or SceneRecallRequest()
        )
