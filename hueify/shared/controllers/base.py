from abc import ABC, abstractmethod
from typing import Self
from uuid import UUID

from pydantic import BaseModel

from hueify.http import HttpClient
from hueify.shared.validation import (
    clamp_brightness,
    clamp_temperature_percentage,
    percentage_to_mirek,
)
from hueify.utils.decorators import time_execution_async
from hueify.utils.logging import LoggingMixin


class ResourceController(ABC, LoggingMixin):
    def __init__(self, client: HttpClient | None = None) -> None:
        self._client = client or HttpClient()

    @classmethod
    @abstractmethod
    @time_execution_async()
    async def from_name(cls, name: str, client: HttpClient | None = None) -> Self:
        pass

    @property
    @abstractmethod
    def id(self) -> UUID:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def _get_resource_endpoint(self) -> str:
        pass

    @abstractmethod
    async def _get_current_brightness(self) -> float:
        pass

    @abstractmethod
    def _create_on_state(self) -> BaseModel:
        pass

    @abstractmethod
    def _create_off_state(self) -> BaseModel:
        pass

    @abstractmethod
    def _create_brightness_state(self, brightness: int) -> BaseModel:
        pass

    @abstractmethod
    def _create_color_temperature_state(self, mirek: int) -> BaseModel:
        pass

    async def turn_on(self) -> None:
        state = self._create_on_state()
        await self._update_state(state)

    async def turn_off(self) -> None:
        state = self._create_off_state()
        await self._update_state(state)

    async def set_brightness(self, brightness_percentage: int) -> None:
        clamped = clamp_brightness(brightness_percentage)
        if clamped != brightness_percentage:
            self.logger.warning(
                f"Brightness {brightness_percentage} is out of range. Clamping to {clamped}."
            )
        await self._update_brightness(clamped)

    async def increase_brightness(self, increment: int) -> None:
        current_brightness = await self._get_current_brightness()
        new_brightness = clamp_brightness(int(current_brightness + increment))
        await self._update_brightness(new_brightness)

    async def decrease_brightness(self, decrement: int) -> None:
        current_brightness = await self._get_current_brightness()
        new_brightness = clamp_brightness(int(current_brightness - decrement))
        await self._update_brightness(new_brightness)

    async def set_color_temperature(self, temperature_percentage: int) -> None:
        clamped = clamp_temperature_percentage(temperature_percentage)
        if clamped != temperature_percentage:
            self.logger.warning(
                f"Temperature {temperature_percentage}% is out of range. Clamping to {clamped}%."
            )
        mirek = percentage_to_mirek(clamped)
        await self._update_color_temperature(mirek)

    async def _update_brightness(self, brightness: int) -> None:
        state = self._create_brightness_state(brightness)
        await self._update_state(state)

    async def _update_color_temperature(self, mirek: int) -> None:
        state = self._create_color_temperature_state(mirek)
        await self._update_state(state)

    async def _update_state(self, state: BaseModel) -> None:
        endpoint = self._get_resource_endpoint()
        await self._client.put(f"{endpoint}/{self.id}", data=state)
