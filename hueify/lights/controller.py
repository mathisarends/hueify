from typing import Self
from uuid import UUID

from hueify.http import HttpClient
from hueify.lights.lookup import LightLookup
from hueify.lights.models import (
    ColorTemperatureState,
    DimmingState,
    LightInfo,
    LightState,
    OnState,
)
from hueify.utils.decorators import time_execution_async
from hueify.utils.logging import LoggingMixin


class LightController(LoggingMixin):
    def __init__(self, light_info: LightInfo, client: HttpClient | None = None) -> None:
        self._light_info = light_info
        self._client = client or HttpClient()

    @classmethod
    @time_execution_async()
    async def from_name(cls, light_name: str, client: HttpClient | None = None) -> Self:
        client = client or HttpClient()
        lookup = LightLookup(client)
        light_info = await lookup.get_light_by_name(light_name)
        return cls(light_info=light_info, client=client)

    @classmethod
    @time_execution_async()
    async def from_id(cls, light_id: UUID, client: HttpClient | None = None) -> Self:
        client = client or HttpClient()
        lookup = LightLookup(client)
        light_info = await lookup.get_light_by_id(light_id)
        return cls(light_info=light_info, client=client)

    @classmethod
    def from_light_info(
        cls, light_info: LightInfo, client: HttpClient | None = None
    ) -> Self:
        client = client or HttpClient()
        return cls(light_info=light_info, client=client)

    @property
    def id(self) -> UUID:
        return self._light_info.id

    @property
    def name(self) -> str:
        return self._light_info.metadata.name

    async def turn_on(self) -> None:
        update = LightState(on=OnState(on=True))
        await self._client.put(f"light/{self.id}", data=update)

    async def turn_off(self) -> None:
        update = LightState(on=OnState(on=False))
        await self._client.put(f"light/{self.id}", data=update)

    async def set_brightness(self, brightness_percentage: float) -> None:
        clamped = self._clamp_brightness(brightness_percentage)
        await self._update_brightness(clamped)

    def _clamp_brightness(self, brightness: float) -> float:
        if brightness < 0:
            self.logger.warning(
                f"Brightness {brightness} is below minimum (0). Clamping to 0."
            )
            return 0.0
        elif brightness > 100:
            self.logger.warning(
                f"Brightness {brightness} is above maximum (100). Clamping to 100."
            )
            return 100.0
        return brightness

    async def _update_brightness(self, brightness: float) -> None:
        update = LightState(
            on=OnState(on=True), dimming=DimmingState(brightness=brightness)
        )
        await self._client.put(f"light/{self.id}", data=update)

    async def increase_brightness(self, increment: float) -> None:
        current_state = await self._get_light_state()
        current_brightness = (
            current_state.dimming.brightness if current_state.dimming else 0.0
        )
        new_brightness = self._clamp_brightness(current_brightness + increment)
        await self._update_brightness(new_brightness)

    async def decrease_brightness(self, decrement: float) -> None:
        current_state = await self._get_light_state()
        current_brightness = (
            current_state.dimming.brightness if current_state.dimming else 0.0
        )
        new_brightness = self._clamp_brightness(current_brightness - decrement)
        await self._update_brightness(new_brightness)

    async def set_color_temperature(self, temperature_percentage: int) -> None:
        clamped = self._clamp_temperature_percentage(temperature_percentage)
        mirek = self._percentage_to_mirek(clamped)
        await self._update_color_temperature(mirek)

    def _percentage_to_mirek(self, percentage: int) -> int:
        return int(153 + (percentage / 100) * (500 - 153))

    def _clamp_temperature_percentage(self, percentage: int) -> int:
        if percentage < 0:
            self.logger.warning(
                f"Temperature {percentage}% is below minimum (0%). Clamping to 0%."
            )
            return 0
        elif percentage > 100:
            self.logger.warning(
                f"Temperature {percentage}% is above maximum (100%). Clamping to 100%."
            )
            return 100
        return percentage

    async def _update_color_temperature(self, mirek: int) -> None:
        update = LightState(
            on=OnState(on=True), color_temperature=ColorTemperatureState(mirek=mirek)
        )
        await self._client.put(f"light/{self.id}", data=update)

    async def get_light_state(self) -> LightState:
        return await self._get_light_state()

    async def _get_light_state(self) -> LightState:
        response = await self._client.get(f"light/{self.id}")
        data = response.get("data", [])
        if not data:
            raise ValueError(f"No light found with id {self.id}")

        light_data = data[0]
        return LightState(
            on=OnState(**light_data["on"]) if "on" in light_data else None,
            dimming=DimmingState(**light_data["dimming"])
            if "dimming" in light_data
            else None,
            color_temperature=ColorTemperatureState(**light_data["color_temperature"])
            if "color_temperature" in light_data
            else None,
        )
