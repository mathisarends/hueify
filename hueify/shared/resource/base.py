from abc import ABC, abstractmethod
from functools import cached_property
from typing import Self
from uuid import UUID

from pydantic import BaseModel

from hueify.http import HttpClient
from hueify.shared.resource.models import ActionResult
from hueify.shared.validation import (
    build_clamped_message,
    clamp_brightness_percentage,
    clamp_temperature_percentage,
    normalize_percentage_input,
    percentage_to_mirek,
)
from hueify.utils.decorators import time_execution_async
from hueify.utils.logging import LoggingMixin


class Resource(ABC, LoggingMixin):
    def __init__(self, client: HttpClient | None = None) -> None:
        self._client = client or HttpClient()

    @classmethod
    @abstractmethod
    async def from_name(cls, name: str, client: HttpClient | None = None) -> Self:
        pass

    @property
    @abstractmethod
    def is_on(self) -> bool:
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

    @property
    @abstractmethod
    def current_brightness(self) -> float:
        pass

    @property
    @abstractmethod
    def current_color_temperature(self) -> int | None:
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
    async def _update_state(self, state: BaseModel) -> None:
        pass

    @time_execution_async()
    async def turn_on(self) -> ActionResult:
        if self.is_on:
            message = "Already on"
        else:
            state = self._create_on_state()
            await self._update_state(state)
            message = "Turned on successfully"

        return ActionResult(message=message)

    @time_execution_async()
    async def turn_off(self) -> ActionResult:
        if not self.is_on:
            message = "Already off"
        else:
            state = self._create_off_state()
            await self._update_state(state)
            message = "Turned off successfully"

        return ActionResult(message=message)

    @time_execution_async()
    async def set_brightness_percentage(self, percentage: float | int) -> ActionResult:
        percentage_int = normalize_percentage_input(percentage)
        clamped_percentage = clamp_brightness_percentage(percentage_int)
        was_clamped = clamped_percentage != percentage_int

        if was_clamped:
            self.logger.warning(
                f"Brightness {percentage_int}% is out of range. Clamping to {clamped_percentage}%."
            )
            message = build_clamped_message(
                property_name="Brightness",
                clamped_value=clamped_percentage,
                requested_value=percentage_int,
                unit="%",
            )
        else:
            message = f"Brightness set to {clamped_percentage}%"

        state = self._create_brightness_state(clamped_percentage)
        await self._update_state(state)
        return ActionResult(
            message=message, clamped=was_clamped, final_value=clamped_percentage
        )

    @time_execution_async()
    async def increase_brightness_percentage(
        self, percentage: float | int
    ) -> ActionResult:
        percentage_int = normalize_percentage_input(percentage)
        target_brightness = int(self.current_brightness + percentage_int)
        new_brightness = clamp_brightness_percentage(target_brightness)
        was_clamped = new_brightness != target_brightness

        if was_clamped:
            message = build_clamped_message(
                property_name="Brightness",
                clamped_value=new_brightness,
                requested_value=target_brightness,
                unit="%",
            )
        else:
            message = f"Brightness increased to {new_brightness}%"

        state = self._create_brightness_state(new_brightness)
        await self._update_state(state)
        return ActionResult(
            message=message, clamped=was_clamped, final_value=new_brightness
        )

    @time_execution_async()
    async def decrease_brightness_percentage(
        self, percentage: float | int
    ) -> ActionResult:
        percentage_int = normalize_percentage_input(percentage)
        target_brightness = int(self.current_brightness - percentage_int)
        new_brightness = clamp_brightness_percentage(target_brightness)
        was_clamped = new_brightness != target_brightness

        if was_clamped:
            message = build_clamped_message(
                property_name="Brightness",
                clamped_value=new_brightness,
                requested_value=target_brightness,
                unit="%",
            )
        else:
            message = f"Brightness decreased to {new_brightness}%"

        state = self._create_brightness_state(new_brightness)
        await self._update_state(state)
        return ActionResult(
            message=message, clamped=was_clamped, final_value=new_brightness
        )

    @time_execution_async()
    async def set_color_temperature_percentage(
        self, percentage: float | int
    ) -> ActionResult:
        percentage_int = normalize_percentage_input(percentage)
        clamped_percentage = clamp_temperature_percentage(percentage_int)
        was_clamped = clamped_percentage != percentage_int

        if was_clamped:
            self.logger.warning(
                f"Temperature {percentage_int}% is out of range. Clamping to {clamped_percentage}%."
            )
            message = build_clamped_message(
                property_name="Temperature",
                clamped_value=clamped_percentage,
                requested_value=percentage_int,
                unit="%",
            )
        else:
            message = f"Temperature set to {clamped_percentage}%"

        mirek = percentage_to_mirek(clamped_percentage)
        state = self._create_color_temperature_state(mirek)
        await self._update_state(state)
        return ActionResult(
            message=message, clamped=was_clamped, final_value=clamped_percentage
        )
