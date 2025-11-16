from typing import Self
from uuid import UUID

from pydantic import BaseModel

from hueify.grouped_lights.lookup import GroupedLightLookup
from hueify.grouped_lights.models import GroupedLightInfo, GroupedLightState
from hueify.http import HttpClient
from hueify.shared.resource.base import Resource
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

    # TODO: This is not fast enough, add caching layer (also this only should use named lookups and cache) | also better typings
    # this should not have a from name method at all, and no lookup aswell

    # maybe even use from name hiere here isntaad of id becauase name is probably cached in the lookup
    """
    state = await client.get_resource(
        f"grouped_light/{id}", resource_type=GroupedLightState
    )
    however this call here should be cached which would be nice (could be for the entire grouped light resource)
    """

    @classmethod
    @time_execution_async()
    async def from_name(cls, name: str, client: HttpClient | None = None) -> Self:
        client = client or HttpClient()
        lookup = GroupedLightLookup(client)
        grouped_light_info = await lookup.get_entity_by_name(name)

        state = await client.get_resource(
            f"grouped_light/{grouped_light_info.id}", resource_type=GroupedLightState
        )
        print("State:", state)

        instance = cls(
            grouped_light_info=grouped_light_info, state=state, client=client
        )
        await instance.ensure_event_subscription()
        return instance

    @classmethod
    @time_execution_async()
    async def from_id(cls, id: UUID, client: HttpClient | None = None) -> Self:
        client = client or HttpClient()

        state = await client.get_resource(
            f"grouped_light/{id}", resource_type=GroupedLightState
        )

        grouped_light_info = GroupedLightInfo(
            id=id,
            type="grouped_light",
            metadata={"name": f"GroupedLight-{id}"},
        )

        return cls(grouped_light_info=grouped_light_info, state=state, client=client)

    @property
    def name(self) -> str:
        return self._grouped_light_info.metadata.name

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
