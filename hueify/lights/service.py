from typing import Self
from uuid import UUID

from pydantic import BaseModel

from hueify.http import HttpClient
from hueify.lights.lookup import LightLookup
from hueify.lights.models import (
    ColorTemperatureState,
    LightDimmingState,
    LightInfo,
    LightOnState,
    LightState,
)
from hueify.shared.controller.base import Resource
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
        return cls(light_info=light_info, state=state, client=client)

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
            on=LightOnState(on=True), dimming=LightDimmingState(brightness=brightness)
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
