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
from hueify.shared.controller.base import ResourceController
from hueify.utils.decorators import time_execution_async


class LightController(ResourceController):
    def __init__(self, light_info: LightInfo, client: HttpClient | None = None) -> None:
        super().__init__(client)
        self._light_info = light_info

    @property
    def is_on(self) -> bool:
        return self._light_info.on.on if self._light_info.on else False

    @classmethod
    @time_execution_async()
    async def from_name(cls, light_name: str, client: HttpClient | None = None) -> Self:
        client = client or HttpClient()
        lookup = LightLookup(client)
        light_info = await lookup.get_light_by_name(light_name)
        return cls(light_info=light_info, client=client)

    @classmethod
    def from_dto(cls, light_info: LightInfo, client: HttpClient | None = None) -> Self:
        client = client or HttpClient()
        return cls(light_info=light_info, client=client)

    @property
    def id(self) -> UUID:
        return self._light_info.id

    @property
    def name(self) -> str:
        return self._light_info.metadata.name

    def _get_resource_endpoint(self) -> str:
        return "light"

    async def _get_current_brightness(self) -> float:
        state = await self._get_light_state()
        return state.dimming.brightness if state.dimming else 0.0

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

    async def _get_current_on_state(self) -> bool:
        return self.is_on

    async def _update_state(self, state: BaseModel) -> None:
        endpoint = self._get_resource_endpoint()
        await self._client.put(f"{endpoint}/{self.id}", data=state)
