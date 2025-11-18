from typing import Self, override

from pydantic import BaseModel

from hueify.http import HttpClient
from hueify.lights.lookup import LightLookup
from hueify.lights.models import (
    LightInfo,
)
from hueify.shared.resource import NamedResourceMixin, Resource
from hueify.sse.events.bus import get_event_bus
from hueify.utils.decorators import time_execution_async


class Light(Resource[LightInfo], NamedResourceMixin):
    @classmethod
    @time_execution_async()
    @override
    async def from_name(cls, light_name: str, client: HttpClient | None = None) -> Self:
        client = client or HttpClient()
        lookup = LightLookup(client)
        light_info = await lookup.get_light_by_name(light_name)

        instance = cls(light_info=light_info, client=client)
        await instance.ensure_event_subscription()
        return instance

    @override
    async def _subscribe_to_events(self) -> None:
        event_bus = await get_event_bus()
        event_bus.subscribe_to_light(
            handler=self._handle_event,
            light_id=self.id,
        )

    @property
    @override
    def name(self) -> str:
        return self._light_info.metadata.name

    @override
    def _get_resource_endpoint(self) -> str:
        return "light"

    @override
    async def _update_remote_state(self, state: BaseModel) -> None:
        endpoint = self._get_resource_endpoint()
        await self._client.put(f"{endpoint}/{self.id}", data=state)
