from typing import Self

from pydantic import BaseModel

from hueify.http import HttpClient
from hueify.lights.lookup import LightLookup
from hueify.lights.models import (
    LightInfo,
)
from hueify.shared.resource.base import Resource
from hueify.sse.events.bus import get_event_bus
from hueify.sse.models import LightEvent
from hueify.utils.decorators import time_execution_async


class Light(Resource[LightInfo]):
    def __init__(
        self,
        light_info: LightInfo,
        client: HttpClient | None = None,
    ) -> None:
        super().__init__(light_info, client)
        self._is_syncing_events = False

    @classmethod
    @time_execution_async()
    async def from_name(cls, light_name: str, client: HttpClient | None = None) -> Self:
        client = client or HttpClient()
        lookup = LightLookup(client)
        light_info = await lookup.get_light_by_name(light_name)

        instance = cls(light_info=light_info, client=client)
        await instance.enable_event_sync()
        return instance

    async def enable_event_sync(self) -> None:
        if self._is_syncing_events:
            return

        event_bus = await get_event_bus()
        event_bus.subscribe_to_light(
            handler=self._sync_state_from_event,
            light_id=self.id,
        )
        self._is_syncing_events = True

    def _sync_state_from_event(self, event: LightEvent) -> None:
        try:
            current_info_data = self._light_info.model_dump()
            event_data = event.model_dump(exclude_unset=True, exclude_none=True)

            current_info_data.update(event_data)
            self._light_info = LightInfo.model_validate(current_info_data)

            self.logger.debug(f"Synced light state for {self.id} from event")
        except Exception as e:
            self.logger.error(
                f"Failed to sync light state from event: {e}", exc_info=True
            )

    @property
    def name(self) -> str:
        return self._light_info.metadata.name

    def _get_resource_endpoint(self) -> str:
        return "light"

    async def _update_remote_state(self, state: BaseModel) -> None:
        endpoint = self._get_resource_endpoint()
        await self._client.put(f"{endpoint}/{self.id}", data=state)
