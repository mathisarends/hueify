from typing import Self
from uuid import UUID

from pydantic import BaseModel

from hueify.grouped_lights.client import GroupedLightClient
from hueify.grouped_lights.models import GroupedLightInfo, GroupedLightState
from hueify.http import HttpClient
from hueify.shared.resource import Resource
from hueify.sse import get_event_bus
from hueify.utils.decorators import time_execution_async


class GroupedLights(Resource[GroupedLightState]):
    def __init__(
        self,
        grouped_light_info: GroupedLightInfo,
        state: GroupedLightState,
        client: HttpClient | None = None,
    ) -> None:
        super().__init__(state, client)
        self._grouped_light_info = grouped_light_info

    @classmethod
    @time_execution_async()
    async def from_id(cls, id: UUID, client: HttpClient | None = None) -> Self:
        client = client or HttpClient()
        grouped_light_client = GroupedLightClient(client)

        grouped_light_info = await grouped_light_client.get_by_id(id)

        state = await client.get_resource(
            f"grouped_light/{id}", resource_type=GroupedLightState
        )

        return cls(grouped_light_info=grouped_light_info, state=state, client=client)

    @property
    def name(self) -> str:
        return self._grouped_light_info.name

    def _get_resource_endpoint(self) -> str:
        return "grouped_light"

    async def _update_remote_state(self, state: BaseModel) -> None:
        endpoint = self._get_resource_endpoint()
        await self._client.put(f"{endpoint}/{self.id}", data=state)

    async def _subscribe_to_events(self) -> None:
        event_bus = await get_event_bus()
        event_bus.subscribe_to_grouped_light(
            handler=self._handle_event,
            group_id=self.id,
        )
