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

_MIN_BRIGHTNESS = 0
_MAX_BRIGHTNESS = 100
_MIN_TEMPERATURE = 0
_MAX_TEMPERATURE = 100
_MIREK_MIN = 153
_MIREK_MAX = 500


class Resource(ABC, Generic[TLightInfo]):
    def __init__(
        self, light_info: TLightInfo, client: HttpClient | None = None
    ) -> None:
        self._light_info = light_info
        self._client = client or HttpClient()
        self._event_subscription_initialized = False

    @abstractmethod
    async def _subscribe_to_events(self) -> None:
        pass

    async def ensure_event_subscription(self) -> None:
        if self._event_subscription_initialized:
            return

        await self._subscribe_to_events()
        self._event_subscription_initialized = True
        logger.info(f"Event subscription initialized for {self.name}")

    def _handle_event(self, event: TLightInfo) -> None:
        try:
            current_info_data = self._light_info.model_dump()
            event_data = event.model_dump(exclude_unset=True, exclude_none=True)

            current_info_data.update(event_data)
            self._light_info = type(self._light_info).model_validate(current_info_data)

            logger.debug(f"Updated state for {self.id} from event")
        except Exception as e:
            logger.error(f"Failed to update state from event: {e}", exc_info=True)

    @property
    def is_on(self) -> bool:
        return self._light_info.on.on

    def id(self) -> UUID:
        return self._light_info.id

    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def _get_resource_endpoint(self) -> str:
        pass

    @property
    def brightness_percentage(self) -> float:
        return self._light_info.dimming.brightness if self._light_info.dimming else 0.0

    @property
    def color_temperature_percentage(self) -> int | None:
        if not self._light_info.color_temperature:
            return None

        mirek = self._light_info.color_temperature.mirek
        return int(((mirek - _MIREK_MIN) / (_MIREK_MAX - _MIREK_MIN)) * 100)

    def _create_on_state(self) -> ControllableLightUpdate:
        return ControllableLightUpdate(on=LightOnState(on=True))

    def _create_off_state(self) -> ControllableLightUpdate:
        return ControllableLightUpdate(on=LightOnState(on=False))

    def _create_brightness_state(self, brightness: int) -> ControllableLightUpdate:
        return ControllableLightUpdate(
            on=LightOnState(on=True), dimming=DimmingState(brightness=brightness)
        )

    def _create_color_temperature_state(self, mirek: int) -> ControllableLightUpdate:
        return ControllableLightUpdate(
            on=LightOnState(on=True),
            color_temperature=ColorTemperatureState(mirek=mirek),
        )

    @abstractmethod
    async def _update_remote_state(self, state: ControllableLightUpdate) -> None:
        pass

    async def turn_on(self) -> ActionResult:
        if self.is_on:
            message = "Already on"
        else:
            state = self._create_on_state()
            await self._update_remote_state(state)
            message = "Turned on successfully"

        return ActionResult(message=message)

    async def turn_off(self) -> ActionResult:
        if not self.is_on:
            message = "Already off"
        else:
            state = self._create_off_state()
            await self._update_remote_state(state)
            message = "Turned off successfully"

        return ActionResult(message=message)

    async def set_brightness_percentage(self, percentage: float | int) -> ActionResult:
        percentage_int = (
            int(percentage * 100)
            if isinstance(percentage, float) and 0 <= percentage <= 1
            else int(percentage)
        )
        clamped = max(_MIN_BRIGHTNESS, min(_MAX_BRIGHTNESS, percentage_int))
        was_clamped = clamped != percentage_int

        if was_clamped:
            logger.warning(
                f"Brightness {percentage_int}% is out of range. Clamping to {clamped}%."
            )
            message = (
                f"Brightness clamped to {clamped}%. "
                f"Requested value {percentage_int}% was out of range."
            )
        else:
            message = f"Brightness set to {clamped}%"

        state = self._create_brightness_state(clamped)
        await self._update_remote_state(state)
        return ActionResult(message=message, clamped=was_clamped, final_value=clamped)

    async def increase_brightness_percentage(
        self, percentage: float | int
    ) -> ActionResult:
        percentage_int = (
            int(percentage * 100)
            if isinstance(percentage, float) and 0 <= percentage <= 1
            else int(percentage)
        )
        target = int(self.brightness_percentage + percentage_int)
        clamped = max(_MIN_BRIGHTNESS, min(_MAX_BRIGHTNESS, target))
        was_clamped = clamped != target

        if was_clamped:
            message = (
                f"Brightness clamped to {clamped}%. "
                f"Requested value {target}% was out of range."
            )
        else:
            message = f"Brightness increased to {clamped}%"

        state = self._create_brightness_state(clamped)
        await self._update_remote_state(state)
        return ActionResult(message=message, clamped=was_clamped, final_value=clamped)

    async def decrease_brightness_percentage(
        self, percentage: float | int
    ) -> ActionResult:
        percentage_int = (
            int(percentage * 100)
            if isinstance(percentage, float) and 0 <= percentage <= 1
            else int(percentage)
        )
        target = int(self.brightness_percentage - percentage_int)
        clamped = max(_MIN_BRIGHTNESS, min(_MAX_BRIGHTNESS, target))
        was_clamped = clamped != target

        if was_clamped:
            message = (
                f"Brightness clamped to {clamped}%. "
                f"Requested value {target}% was out of range."
            )
        else:
            message = f"Brightness decreased to {clamped}%"

        state = self._create_brightness_state(clamped)
        await self._update_remote_state(state)
        return ActionResult(message=message, clamped=was_clamped, final_value=clamped)

    async def set_color_temperature_percentage(
        self, percentage: float | int
    ) -> ActionResult:
        percentage_int = (
            int(percentage * 100)
            if isinstance(percentage, float) and 0 <= percentage <= 1
            else int(percentage)
        )
        clamped = max(_MIN_TEMPERATURE, min(_MAX_TEMPERATURE, percentage_int))
        was_clamped = clamped != percentage_int

        if was_clamped:
            logger.warning(
                f"Temperature {percentage_int}% is out of range. Clamping to {clamped}%."
            )
            message = (
                f"Temperature clamped to {clamped}%. "
                f"Requested value {percentage_int}% was out of range."
            )
        else:
            message = f"Temperature set to {clamped}%"

        mirek = int(_MIREK_MIN + (clamped / 100) * (_MIREK_MAX - _MIREK_MIN))
        state = self._create_color_temperature_state(mirek)
        await self._update_remote_state(state)
        return ActionResult(message=message, clamped=was_clamped, final_value=clamped)
