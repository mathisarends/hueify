from typing import Self

from pydantic import BaseModel

from hueify.events import get_event_bus
from hueify.http import HttpClient
from hueify.lights.lookup import LightLookup
from hueify.lights.models import (
    LightInfo,
)
from hueify.shared.resource import NamedResourceMixin, Resource


class Light(Resource[LightInfo], NamedResourceMixin):
    @classmethod
    async def from_name(cls, light_name: str, client: HttpClient | None = None) -> Self:
        client = client or HttpClient()
        lookup = LightLookup(client)
        light_info = await lookup.get_light_by_name(light_name)

        instance = cls(light_info=light_info, client=client)
        await instance.ensure_event_subscription()
        return instance

    async def _subscribe_to_events(self) -> None:
        event_bus = await get_event_bus()
        event_bus.subscribe_to_light(
            handler=self._handle_event,
            light_id=self.id,
        )

    @property
    def name(self) -> str:
        return self._light_info.metadata.name

    def _get_resource_endpoint(self) -> str:
        return "light"

    async def _update_remote_state(self, state: BaseModel) -> None:
        endpoint = self._get_resource_endpoint()
        await self._client.put(f"{endpoint}/{self.id}", data=state)
