from functools import cached_property
from typing import Self, override
from uuid import UUID

from pydantic import BaseModel

from hueify.grouped_lights.lookup import GroupedLightLookup
from hueify.grouped_lights.models import GroupedLightInfo
from hueify.http import HttpClient
from hueify.shared.resource import Resource
from hueify.sse import get_event_bus
from hueify.utils.decorators import time_execution_async


class GroupedLights(Resource[GroupedLightInfo]):
    @classmethod
    @time_execution_async()
    async def from_id(cls, id: UUID, client: HttpClient | None = None) -> Self:
        client = client or HttpClient()
        lookup = GroupedLightLookup(client=client)

        grouped_light_info = await lookup.get_entity_by_id(id)

        if not grouped_light_info:
            raise ValueError(f"GroupedLight with id {id} not found")

        return cls(light_info=grouped_light_info, client=client)

    @cached_property
    @override
    def name(self) -> str:
        return self._light_info.name

    @override
    def _get_resource_endpoint(self) -> str:
        return "grouped_light"

    @override
    async def _update_remote_state(self, state: BaseModel) -> None:
        endpoint = self._get_resource_endpoint()
        await self._client.put(f"{endpoint}/{self.id}", data=state)

    @override
    async def _subscribe_to_events(self) -> None:
        event_bus = await get_event_bus()
        event_bus.subscribe_to_grouped_light(
            handler=self._handle_event,
            group_id=self.id,
        )
