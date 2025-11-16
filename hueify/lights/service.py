from typing import Self
from uuid import UUID

from pydantic import BaseModel

from hueify.http import HttpClient
from hueify.lights.lookup import LightLookup
from hueify.lights.models import (
    ColorTemperatureState,
    LightInfo,
    LightOnState,
    LightState,
)
from hueify.shared.resource.base import Resource
from hueify.shared.resource.models import DimmingState
from hueify.sse.events.bus import get_event_bus
from hueify.sse.models import LightEvent
from hueify.utils.decorators import time_execution_async


class Light(Resource):
    def __init__(
        self,
        light_info: LightInfo,
        state: LightState,
        client: HttpClient | None = None,
    ) -> None:
        super().__init__(client)
        self._light_info = light_info
        self._state = state
        self._is_syncing_events = False

    @property
    def is_on(self) -> bool:
        return self._state.on.on if self._state.on else False

    @property
    def current_brightness(self) -> float:
        return self._state.dimming.brightness if self._state.dimming else 0.0

    @property
    def current_color_temperature(self) -> int | None:
        if self._state.color_temperature:
            return self._state.color_temperature.mirek
        return None

    @classmethod
    @time_execution_async()
    async def from_name(cls, light_name: str, client: HttpClient | None = None) -> Self:
        client = client or HttpClient()
        lookup = LightLookup(client)
        light_info = await lookup.get_light_by_name(light_name)

        state = await client.get_resource(f"light/{light_info.id}", LightState)
        instance = cls(light_info=light_info, state=state, client=client)
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
        if event.on is not None:
            self._update_on_state(event.on.on)

        if event.dimming is not None:
            self._update_dimming_state(event.dimming.brightness)

        if event.color_temperature is not None:
            self._update_color_temperature_state(
                event.color_temperature.mirek,
                event.color_temperature.mirek_valid,
            )

    def _update_on_state(self, on: bool) -> None:
        if self._state.on is None:
            self._state.on = LightOnState(on=on)
        else:
            self._state.on.on = on

    def _update_dimming_state(self, brightness: float) -> None:
        if self._state.dimming is None:
            self._state.dimming = DimmingState(brightness=brightness)
        else:
            self._state.dimming.brightness = brightness

    def _update_color_temperature_state(
        self, mirek: int | None, mirek_valid: bool
    ) -> None:
        if self._state.color_temperature is None:
            self._state.color_temperature = ColorTemperatureState(
                mirek=mirek,
                mirek_valid=mirek_valid,
            )
        else:
            self._state.color_temperature.mirek = mirek
            self._state.color_temperature.mirek_valid = mirek_valid

    @property
    def id(self) -> UUID:
        return self._light_info.id

    @property
    def name(self) -> str:
        return self._light_info.metadata.name

    def _get_resource_endpoint(self) -> str:
        return "light"

    def _create_on_state(self) -> BaseModel:
        return LightState(on=LightOnState(on=True))

    def _create_off_state(self) -> BaseModel:
        return LightState(on=LightOnState(on=False))

    def _create_brightness_state(self, brightness: int) -> BaseModel:
        return LightState(
            on=LightOnState(on=True), dimming=DimmingState(brightness=brightness)
        )

    def _create_color_temperature_state(self, mirek: int) -> BaseModel:
        return LightState(
            on=LightOnState(on=True),
            color_temperature=ColorTemperatureState(mirek=mirek),
        )

    async def get_light_state(self) -> LightState:
        return await self._get_light_state()

    async def _get_light_state(self) -> LightState:
        return await self._client.get_resource(f"light/{self.id}", LightState)

    async def _update_state(self, state: BaseModel) -> None:
        endpoint = self._get_resource_endpoint()
        await self._client.put(f"{endpoint}/{self.id}", data=state)
        self._state = await self._get_light_state()
