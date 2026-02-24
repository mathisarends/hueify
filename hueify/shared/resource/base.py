import logging
from abc import ABC, abstractmethod
from functools import cached_property
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
from hueify.shared.validation import (
    build_clamped_message,
    clamp_brightness_percentage,
    clamp_temperature_percentage,
    mirek_to_percentage,
    normalize_percentage_input,
    percentage_to_mirek,
)
from hueify.utils.decorators import time_execution_async

logger = logging.getLogger(__name__)


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

    @time_execution_async()
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

    @cached_property
    def id(self) -> UUID:
        return self._light_info.id

    @cached_property
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

        return mirek_to_percentage(self._light_info.color_temperature.mirek)

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

    @time_execution_async()
    async def turn_on(self) -> ActionResult:
        if self.is_on:
            message = "Already on"
        else:
            state = self._create_on_state()
            await self._update_remote_state(state)
            message = "Turned on successfully"

        return ActionResult(message=message)

    @time_execution_async()
    async def turn_off(self) -> ActionResult:
        if not self.is_on:
            message = "Already off"
        else:
            state = self._create_off_state()
            await self._update_remote_state(state)
            message = "Turned off successfully"

        return ActionResult(message=message)

    @time_execution_async()
    async def set_brightness_percentage(self, percentage: float | int) -> ActionResult:
        percentage_int = normalize_percentage_input(percentage)
        clamped_percentage = clamp_brightness_percentage(percentage_int)
        was_clamped = clamped_percentage != percentage_int

        if was_clamped:
            logger.warning(
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
        await self._update_remote_state(state)
        return ActionResult(
            message=message, clamped=was_clamped, final_value=clamped_percentage
        )

    @time_execution_async()
    async def increase_brightness_percentage(
        self, percentage: float | int
    ) -> ActionResult:
        percentage_int = normalize_percentage_input(percentage)
        target_brightness = int(self.brightness_percentage + percentage_int)
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
        await self._update_remote_state(state)
        return ActionResult(
            message=message, clamped=was_clamped, final_value=new_brightness
        )

    @time_execution_async()
    async def decrease_brightness_percentage(
        self, percentage: float | int
    ) -> ActionResult:
        percentage_int = normalize_percentage_input(percentage)
        target_brightness = int(self.brightness_percentage - percentage_int)
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
        await self._update_remote_state(state)
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
            logger.warning(
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
        await self._update_remote_state(state)
        return ActionResult(
            message=message, clamped=was_clamped, final_value=clamped_percentage
        )
