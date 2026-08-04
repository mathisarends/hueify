from pydantic import TypeAdapter

from hueify.http import HttpClient
from hueify.models import (
    HueApiResponse,
    ResourceIdentifier,
    Scene,
    SceneRecallRequest,
    SceneUpdate,
)
from hueify.resources.base import ResourceId, ResourceNamespace


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
