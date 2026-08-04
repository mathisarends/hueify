from uuid import UUID

from pydantic import TypeAdapter

from hueify.errors import ResourceNotFoundError
from hueify.http import HttpClient
from hueify.models import (
    Group,
    GroupedLight,
    GroupUpdate,
    HueApiResponse,
    Light,
    LightUpdate,
    ResourceIdentifier,
    ResourceType,
    Room,
    Scene,
    Zone,
)
from hueify.resources.base import ResourceId, ResourceNamespace
from hueify.resources.controls import LightCommands
from hueify.resources.lights import LightNamespace
from hueify.resources.scenes import SceneNamespace

GROUPED_LIGHT_RESOURCE_TYPE = "grouped_light"

_grouped_light_adapter = TypeAdapter(HueApiResponse[GroupedLight])


class GroupNamespace[TGroup: Group](LightCommands, ResourceNamespace[TGroup]):
    """Shared behaviour of the room and zone endpoints.

    Light commands address the group's ``grouped_light`` service, so a room
    or zone is switched in one bridge call instead of light by light.
    """

    def __init__(
        self,
        resource_type: str,
        response_adapter: TypeAdapter[HueApiResponse[TGroup]],
        http_client: HttpClient,
    ) -> None:
        super().__init__(resource_type, response_adapter, http_client)
        self._lights = LightNamespace(http_client)
        self._scenes = SceneNamespace(http_client)

    async def create(self, data: GroupUpdate) -> HueApiResponse[ResourceIdentifier]:
        return await self._create(data)

    async def update(
        self, group_id: ResourceId, data: GroupUpdate
    ) -> HueApiResponse[ResourceIdentifier]:
        return await self._update(group_id, data)

    async def delete(self, group_id: ResourceId) -> HueApiResponse[ResourceIdentifier]:
        return await self._delete(group_id)

    async def lights(self, group_id: ResourceId) -> list[Light]:
        group = await self.get_one(group_id)
        member_ids = {child.rid for child in group.children}
        return [
            light
            for light in (await self._lights.list()).data
            if light.id in member_ids or light.owner.rid in member_ids
        ]

    async def scenes(self, group_id: ResourceId) -> list[Scene]:
        group = await self.get_one(group_id)
        return [
            scene
            for scene in (await self._scenes.list()).data
            if scene.group.rid == group.id
        ]

    async def grouped_light_id(self, group_id: ResourceId) -> UUID:
        group = await self.get_one(group_id)
        for service in group.services:
            if service.rtype is ResourceType.GROUPED_LIGHT:
                return service.rid
        raise ResourceNotFoundError(
            f"{self.resource_type} {group_id} has no grouped light service"
        )

    async def grouped_light(self, group_id: ResourceId) -> GroupedLight:
        grouped_light_id = await self.grouped_light_id(group_id)
        response = await self._http_client.get(
            f"{GROUPED_LIGHT_RESOURCE_TYPE}/{grouped_light_id}", _grouped_light_adapter
        )
        if not response.data:
            raise ResourceNotFoundError(f"No grouped light with ID {grouped_light_id}")
        return response.data[0]

    async def apply(
        self, group_id: ResourceId, update: LightUpdate
    ) -> HueApiResponse[ResourceIdentifier]:
        grouped_light_id = await self.grouped_light_id(group_id)
        return await self._http_client.put(
            f"{GROUPED_LIGHT_RESOURCE_TYPE}/{grouped_light_id}", update
        )

    async def is_on(self, group_id: ResourceId) -> bool:
        on_state = (await self.grouped_light(group_id)).on
        return on_state is not None and on_state.on


class RoomNamespace(GroupNamespace[Room]):
    def __init__(self, http_client: HttpClient) -> None:
        super().__init__("room", TypeAdapter(HueApiResponse[Room]), http_client)


class ZoneNamespace(GroupNamespace[Zone]):
    def __init__(self, http_client: HttpClient) -> None:
        super().__init__("zone", TypeAdapter(HueApiResponse[Zone]), http_client)
