import logging
from abc import ABC, abstractmethod
from typing import Generic
from uuid import UUID

from hueify.http import HttpClient
from hueify.shared.resource.models import (
    ActionResult,
    ColorTemperatureState,
    ControllableLightUpdate,
    DimmingState,
    LightOnState,
    TLightInfo,
)

logger = logging.getLogger(__name__)


class Resource(ABC, Generic[TLightInfo]):
    _MIN_BRIGHTNESS = 0
    _MAX_BRIGHTNESS = 100
    _MIN_TEMPERATURE = 0
    _MAX_TEMPERATURE = 100
    _MIREK_MIN = 153
    _MIREK_MAX = 500

    def __init__(
        self, light_info: TLightInfo, client: HttpClient | None = None
    ) -> None:
        self._light_info = light_info
        self._client = client or HttpClient()

    @property
    def is_on(self) -> bool:
        return self._light_info.on.on

    @property
    def brightness_percentage(self) -> float:
        return self._light_info.dimming.brightness if self._light_info.dimming else 0.0

    @property
    def color_temperature_percentage(self) -> int | None:
        if not self._light_info.color_temperature:
            return None

        mirek = self._light_info.color_temperature.mirek
        return int(
            ((mirek - self._MIREK_MIN) / (self._MIREK_MAX - self._MIREK_MIN)) * 100
        )

    def id(self) -> UUID:
        return self._light_info.id

    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def _get_resource_endpoint(self) -> str:
        pass

    async def turn_on(self) -> ActionResult:
        if self.is_on:
            return ActionResult(message="Already on")

        await self._update_remote_state(self._create_on_state())
        return ActionResult(message="Turned on successfully")

    def _create_on_state(self) -> ControllableLightUpdate:
        return ControllableLightUpdate(on=LightOnState(on=True))

    async def turn_off(self) -> ActionResult:
        if not self.is_on:
            return ActionResult(message="Already off")

        await self._update_remote_state(self._create_off_state())
        return ActionResult(message="Turned off successfully")

    def _create_off_state(self) -> ControllableLightUpdate:
        return ControllableLightUpdate(on=LightOnState(on=False))

    async def set_brightness(self, percentage: float | int) -> ActionResult:
        percentage_int = self._normalize_percentage(percentage)
        clamped = max(self._MIN_BRIGHTNESS, min(self._MAX_BRIGHTNESS, percentage_int))
        was_clamped = clamped != percentage_int

        if was_clamped:
            logger.warning(
                f"Brightness {percentage_int}% is out of range. Clamping to {clamped}%."
            )
            message = f"Brightness clamped to {clamped}%. Requested value {percentage_int}% was out of range."
        else:
            message = f"Brightness set to {clamped}%"

        await self._update_remote_state(self._create_brightness_state(clamped))
        return ActionResult(message=message, clamped=was_clamped, final_value=clamped)

    async def increase_brightness(self, percentage: float | int) -> ActionResult:
        percentage_int = self._normalize_percentage(percentage)
        target = int(self.brightness_percentage + percentage_int)
        clamped = max(self._MIN_BRIGHTNESS, min(self._MAX_BRIGHTNESS, target))
        was_clamped = clamped != target

        message = (
            f"Brightness clamped to {clamped}%. Requested value {target}% was out of range."
            if was_clamped
            else f"Brightness increased to {clamped}%"
        )

        await self._update_remote_state(self._create_brightness_state(clamped))
        return ActionResult(message=message, clamped=was_clamped, final_value=clamped)

    async def decrease_brightness(self, percentage: float | int) -> ActionResult:
        percentage_int = self._normalize_percentage(percentage)
        target = int(self.brightness_percentage - percentage_int)
        clamped = max(self._MIN_BRIGHTNESS, min(self._MAX_BRIGHTNESS, target))
        was_clamped = clamped != target

        message = (
            f"Brightness clamped to {clamped}%. Requested value {target}% was out of range."
            if was_clamped
            else f"Brightness decreased to {clamped}%"
        )

        await self._update_remote_state(self._create_brightness_state(clamped))
        return ActionResult(message=message, clamped=was_clamped, final_value=clamped)

    def _create_brightness_state(self, brightness: int) -> ControllableLightUpdate:
        return ControllableLightUpdate(
            on=LightOnState(on=True), dimming=DimmingState(brightness=brightness)
        )

    def _normalize_percentage(self, percentage: float | int) -> int:
        if isinstance(percentage, float) and 0 <= percentage <= 1:
            return int(percentage * 100)
        return int(percentage)

    async def set_color_temperature(self, percentage: float | int) -> ActionResult:
        percentage_int = self._normalize_percentage(percentage)
        clamped = max(self._MIN_TEMPERATURE, min(self._MAX_TEMPERATURE, percentage_int))
        was_clamped = clamped != percentage_int

        if was_clamped:
            logger.warning(
                f"Temperature {percentage_int}% is out of range. Clamping to {clamped}%."
            )
            message = f"Temperature clamped to {clamped}%. Requested value {percentage_int}% was out of range."
        else:
            message = f"Temperature set to {clamped}%"

        mirek = int(
            self._MIREK_MIN + (clamped / 100) * (self._MIREK_MAX - self._MIREK_MIN)
        )
        await self._update_remote_state(self._create_color_temperature_state(mirek))
        return ActionResult(message=message, clamped=was_clamped, final_value=clamped)

    def _create_color_temperature_state(self, mirek: int) -> ControllableLightUpdate:
        return ControllableLightUpdate(
            on=LightOnState(on=True),
            color_temperature=ColorTemperatureState(mirek=mirek),
        )

    @abstractmethod
    async def _update_remote_state(self, state: ControllableLightUpdate) -> None:
        pass
