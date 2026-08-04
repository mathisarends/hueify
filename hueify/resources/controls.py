from abc import ABC, abstractmethod
from datetime import timedelta

from hueify.color import hex_to_rgb, kelvin_to_mirek, rgb_to_xy
from hueify.models import (
    AlertState,
    ColorState,
    ColorTemperatureState,
    ColorXY,
    DimmingDelta,
    DimmingDeltaAction,
    DimmingState,
    DynamicsState,
    HueApiResponse,
    LightUpdate,
    OnState,
    ResourceIdentifier,
)
from hueify.resources.base import ResourceId

type Transition = float | timedelta

_DEFAULT_BRIGHTNESS_STEP = 10.0
_IDENTIFY_ALERT_ACTION = "breathe"


def _build_light_update(
    *,
    on: bool | None = None,
    brightness: float | None = None,
    color: ColorXY | None = None,
    kelvin: int | None = None,
    mirek: int | None = None,
    transition: Transition | None = None,
) -> LightUpdate:
    if kelvin is not None and mirek is not None:
        raise ValueError("Pass either kelvin or mirek, not both")
    if color is not None and (kelvin is not None or mirek is not None):
        raise ValueError("A light shows either a color or a color temperature")

    if kelvin is not None:
        mirek = kelvin_to_mirek(kelvin)

    return LightUpdate(
        on=None if on is None else OnState(on=on),
        dimming=None if brightness is None else DimmingState(brightness=brightness),
        color=None if color is None else ColorState(xy=color),
        color_temperature=(
            None if mirek is None else ColorTemperatureState(mirek=mirek)
        ),
        dynamics=(
            None
            if transition is None
            else DynamicsState(duration=_transition_to_milliseconds(transition))
        ),
    )


def _transition_to_milliseconds(transition: Transition) -> int:
    seconds = (
        transition.total_seconds()
        if isinstance(transition, timedelta)
        else float(transition)
    )
    if seconds < 0:
        raise ValueError("A transition cannot be negative")
    return round(seconds * 1000)


class LightCommands(ABC):
    """Task-oriented commands shared by lights, rooms and zones.

    Every ``set_*`` command switches the target on, because that is what
    asking for a brightness or a color implies. ``set_state`` sends exactly
    what it is given and nothing else.
    """

    @abstractmethod
    async def apply(
        self, resource_id: ResourceId, update: LightUpdate
    ) -> HueApiResponse[ResourceIdentifier]: ...

    @abstractmethod
    async def is_on(self, resource_id: ResourceId) -> bool: ...

    async def set_state(
        self,
        resource_id: ResourceId,
        *,
        on: bool | None = None,
        brightness: float | None = None,
        color: ColorXY | None = None,
        kelvin: int | None = None,
        mirek: int | None = None,
        transition: Transition | None = None,
    ) -> HueApiResponse[ResourceIdentifier]:
        return await self.apply(
            resource_id,
            _build_light_update(
                on=on,
                brightness=brightness,
                color=color,
                kelvin=kelvin,
                mirek=mirek,
                transition=transition,
            ),
        )

    async def turn_on(
        self,
        resource_id: ResourceId,
        *,
        brightness: float | None = None,
        kelvin: int | None = None,
        transition: Transition | None = None,
    ) -> HueApiResponse[ResourceIdentifier]:
        return await self.set_state(
            resource_id,
            on=True,
            brightness=brightness,
            kelvin=kelvin,
            transition=transition,
        )

    async def turn_off(
        self,
        resource_id: ResourceId,
        *,
        transition: Transition | None = None,
    ) -> HueApiResponse[ResourceIdentifier]:
        return await self.set_state(resource_id, on=False, transition=transition)

    async def toggle(
        self,
        resource_id: ResourceId,
        *,
        transition: Transition | None = None,
    ) -> HueApiResponse[ResourceIdentifier]:
        currently_on = await self.is_on(resource_id)
        return await self.set_state(
            resource_id, on=not currently_on, transition=transition
        )

    async def set_brightness(
        self,
        resource_id: ResourceId,
        brightness: float,
        *,
        transition: Transition | None = None,
    ) -> HueApiResponse[ResourceIdentifier]:
        if brightness == 0:
            return await self.turn_off(resource_id, transition=transition)
        return await self.set_state(
            resource_id, on=True, brightness=brightness, transition=transition
        )

    async def brighten(
        self,
        resource_id: ResourceId,
        by: float = _DEFAULT_BRIGHTNESS_STEP,
    ) -> HueApiResponse[ResourceIdentifier]:
        return await self._step_brightness(resource_id, DimmingDeltaAction.UP, by)

    async def dim(
        self,
        resource_id: ResourceId,
        by: float = _DEFAULT_BRIGHTNESS_STEP,
    ) -> HueApiResponse[ResourceIdentifier]:
        return await self._step_brightness(resource_id, DimmingDeltaAction.DOWN, by)

    async def set_rgb(
        self,
        resource_id: ResourceId,
        red: int,
        green: int,
        blue: int,
        *,
        brightness: float | None = None,
        transition: Transition | None = None,
    ) -> HueApiResponse[ResourceIdentifier]:
        return await self._show_color(
            resource_id, rgb_to_xy((red, green, blue)), brightness, transition
        )

    async def set_hex(
        self,
        resource_id: ResourceId,
        hex_color: str,
        *,
        brightness: float | None = None,
        transition: Transition | None = None,
    ) -> HueApiResponse[ResourceIdentifier]:
        return await self._show_color(
            resource_id, rgb_to_xy(hex_to_rgb(hex_color)), brightness, transition
        )

    async def set_color_temperature(
        self,
        resource_id: ResourceId,
        kelvin: int,
        *,
        brightness: float | None = None,
        transition: Transition | None = None,
    ) -> HueApiResponse[ResourceIdentifier]:
        return await self.set_state(
            resource_id,
            on=True,
            kelvin=kelvin,
            brightness=brightness,
            transition=transition,
        )

    async def identify(
        self, resource_id: ResourceId
    ) -> HueApiResponse[ResourceIdentifier]:
        return await self.apply(
            resource_id, LightUpdate(alert=AlertState(action=_IDENTIFY_ALERT_ACTION))
        )

    async def _show_color(
        self,
        resource_id: ResourceId,
        xy: ColorXY,
        brightness: float | None,
        transition: Transition | None,
    ) -> HueApiResponse[ResourceIdentifier]:
        return await self.set_state(
            resource_id,
            on=True,
            color=xy,
            brightness=brightness,
            transition=transition,
        )

    async def _step_brightness(
        self,
        resource_id: ResourceId,
        action: DimmingDeltaAction,
        by: float,
    ) -> HueApiResponse[ResourceIdentifier]:
        return await self.apply(
            resource_id,
            LightUpdate(dimming_delta=DimmingDelta(action=action, brightness_delta=by)),
        )
