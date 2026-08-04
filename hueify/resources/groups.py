from pydantic import TypeAdapter

from hueify.http import HttpClient
from hueify.models import (
    Group,
    GroupUpdate,
    HueApiResponse,
    ResourceIdentifier,
    Room,
    Zone,
)
from hueify.resources.base import ResourceId, ResourceNamespace


class GroupNamespace[TGroup: Group](ResourceNamespace[TGroup]):
    """Shared behaviour of the room and zone endpoints."""

    async def create(self, data: GroupUpdate) -> HueApiResponse[ResourceIdentifier]:
        return await self._create(data)

    async def update(
        self, group_id: ResourceId, data: GroupUpdate
    ) -> HueApiResponse[ResourceIdentifier]:
        return await self._update(group_id, data)

    async def delete(self, group_id: ResourceId) -> HueApiResponse[ResourceIdentifier]:
        return await self._delete(group_id)


class RoomNamespace(GroupNamespace[Room]):
    def __init__(self, http_client: HttpClient) -> None:
        super().__init__("room", TypeAdapter(HueApiResponse[Room]), http_client)


class ZoneNamespace(GroupNamespace[Zone]):
    def __init__(self, http_client: HttpClient) -> None:
        super().__init__("zone", TypeAdapter(HueApiResponse[Zone]), http_client)
