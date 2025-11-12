from abc import ABC, abstractmethod
from functools import cached_property
from typing import Self
from uuid import UUID

from pydantic import BaseModel

from hueify.http import HttpClient
from hueify.shared.controllers.models import ActionResult
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

    @cached_property
    @abstractmethod
    def id(self) -> UUID:
        pass

    @cached_property
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

    @abstractmethod
    async def _get_current_on_state(self) -> bool:
        pass

    async def turn_on(self) -> ActionResult:
        was_already_on = await self._get_current_on_state()

        if was_already_on:
            message = "Already on"
        else:
            state = self._create_on_state()
            await self._update_state(state)
            message = "Turned on successfully"

        return ActionResult(message=message)

    async def turn_off(self) -> ActionResult:
        was_already_off = not await self._get_current_on_state()

        if was_already_off:
            message = "Already off"
        else:
            state = self._create_off_state()
            await self._update_state(state)
            message = "Turned off successfully"

        return ActionResult(message=message)

    async def set_brightness(self, brightness_percentage: int) -> ActionResult:
        clamped_brightness = clamp_brightness(brightness_percentage)
        was_clamped = clamped_brightness != brightness_percentage

        if was_clamped:
            self.logger.warning(
                f"Brightness {brightness_percentage} is out of range. Clamping to {clamped_brightness}."
            )
            message = self._build_clamped_message(
                property_name="Brightness",
                clamped_value=clamped_brightness,
                requested_value=brightness_percentage,
            )
        else:
            message = f"Brightness set to {clamped_brightness}"

        await self._update_brightness(clamped_brightness)
        return ActionResult(
            message=message, clamped=was_clamped, final_value=clamped_brightness
        )

    async def increase_brightness(self, increment: int) -> ActionResult:
        current_brightness = await self._get_current_brightness()
        target_brightness = int(current_brightness + increment)
        new_brightness = clamp_brightness(target_brightness)
        was_clamped = new_brightness != target_brightness

        if was_clamped:
            message = self._build_clamped_message(
                property_name="Brightness",
                clamped_value=new_brightness,
                requested_value=target_brightness,
            )
        else:
            message = f"Brightness increased to {new_brightness}"

        await self._update_brightness(new_brightness)
        return ActionResult(
            message=message, clamped=was_clamped, final_value=new_brightness
        )

    async def decrease_brightness(self, decrement: int) -> ActionResult:
        current_brightness = await self._get_current_brightness()
        target_brightness = int(current_brightness - decrement)
        new_brightness = clamp_brightness(target_brightness)
        was_clamped = new_brightness != target_brightness

        if was_clamped:
            message = self._build_clamped_message(
                property_name="Brightness",
                clamped_value=new_brightness,
                requested_value=target_brightness,
            )
        else:
            message = f"Brightness decreased to {new_brightness}"

        await self._update_brightness(new_brightness)
        return ActionResult(
            message=message, clamped=was_clamped, final_value=new_brightness
        )

    async def set_color_temperature(self, temperature_percentage: int) -> ActionResult:
        clamped_temperature = clamp_temperature_percentage(temperature_percentage)
        was_clamped = clamped_temperature != temperature_percentage

        if was_clamped:
            self.logger.warning(
                f"Temperature {temperature_percentage}% is out of range. Clamping to {clamped_temperature}%."
            )
            message = self._build_clamped_message(
                property_name="Temperature",
                clamped_value=clamped_temperature,
                requested_value=temperature_percentage,
                unit="%",
            )
        else:
            message = f"Temperature set to {clamped_temperature}%"

        mirek = percentage_to_mirek(clamped_temperature)
        await self._update_color_temperature(mirek)
        return ActionResult(
            message=message, clamped=was_clamped, final_value=clamped_temperature
        )

    def _build_clamped_message(
        self,
        property_name: str,
        clamped_value: int,
        requested_value: int,
        unit: str = "",
    ) -> str:
        return (
            f"{property_name} clamped to {clamped_value}{unit}. "
            f"Requested value {requested_value}{unit} was out of range."
        )

    async def _update_brightness(self, brightness: int) -> None:
        state = self._create_brightness_state(brightness)
        await self._update_state(state)

    async def _update_color_temperature(self, mirek: int) -> None:
        state = self._create_color_temperature_state(mirek)
        await self._update_state(state)

    async def _update_state(self, state: BaseModel) -> None:
        endpoint = self._get_resource_endpoint()
        await self._client.put(f"{endpoint}/{self.id}", data=state)
