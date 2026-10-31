from collections.abc import Sequence
from typing import Literal

from hueify.color import kelvin_to_mirek
from hueify.http import HttpClient
from hueify.models import (
    ColorState,
    ColorTemperatureState,
    ColorXY,
    EffectAction,
    EffectParameters,
    EffectsV2Update,
    GradientPoint,
    GradientUpdate,
    HueApiResponse,
    Light,
    LightUpdate,
    OnState,
    PowerupState,
    ResourceIdentifier,
    TimedEffectsState,
)
from hueify.resources.base import ResourceId, UpdateNamespace
from hueify.resources.controls import (
    LightCommands,
    Transition,
    _transition_to_milliseconds,
)


class LightNamespace(LightCommands, UpdateNamespace[Light, LightUpdate]):
    def __init__(self, http_client: HttpClient) -> None:
        super().__init__("light", Light, LightUpdate, http_client)

    async def update(
        self, light_id: ResourceId, data: LightUpdate
    ) -> HueApiResponse[ResourceIdentifier]:
        return await super().update(light_id, data)

    async def apply(
        self, light_id: ResourceId, update: LightUpdate
    ) -> HueApiResponse[ResourceIdentifier]:
        return await self.update(light_id, update)

    async def is_on(self, light_id: ResourceId) -> bool:
        return (await self.get_one(light_id)).on.on

    async def set_effect(
        self,
        light_id: ResourceId,
        effect: str,
        *,
        color: ColorXY | None = None,
        kelvin: int | None = None,
        speed: float | None = None,
    ) -> HueApiResponse[ResourceIdentifier]:
        """Use effects_v2; available effects and parameters depend on the light."""
        if color is not None and kelvin is not None:
            raise ValueError("Pass either a color or a color temperature")
        parameters = None
        if color is not None or kelvin is not None or speed is not None:
            parameters = EffectParameters(
                color=None if color is None else ColorState(xy=color),
                color_temperature=None
                if kelvin is None
                else ColorTemperatureState(mirek=kelvin_to_mirek(kelvin)),
                speed=speed,
            )
        return await self.update(
            light_id,
            LightUpdate(
                on=OnState(on=True),
                effects_v2=EffectsV2Update(
                    action=EffectAction(effect=effect, parameters=parameters)
                ),
            ),
        )

    async def stop_effect(
        self, light_id: ResourceId
    ) -> HueApiResponse[ResourceIdentifier]:
        return await self.update(
            light_id,
            LightUpdate(
                effects_v2=EffectsV2Update(action=EffectAction(effect="no_effect"))
            ),
        )

    async def set_gradient(
        self,
        light_id: ResourceId,
        colors: Sequence[ColorXY],
        *,
        mode: Literal[
            "interpolated_palette", "interpolated_palette_mirrored", "random_pixelated"
        ]
        | None = None,
    ) -> HueApiResponse[ResourceIdentifier]:
        if not 2 <= len(colors) <= 5:
            raise ValueError("A gradient needs between 2 and 5 color points")
        if mode is not None and mode not in {
            "interpolated_palette",
            "interpolated_palette_mirrored",
            "random_pixelated",
        }:
            raise ValueError("Unknown gradient mode")
        return await self.update(
            light_id,
            LightUpdate(
                on=OnState(on=True),
                gradient=GradientUpdate(
                    points=[GradientPoint(color=ColorState(xy=xy)) for xy in colors],
                    mode=mode,
                ),
            ),
        )

    async def set_timed_effect(
        self,
        light_id: ResourceId,
        effect: str,
        *,
        duration: Transition | None = None,
    ) -> HueApiResponse[ResourceIdentifier]:
        if effect != "no_effect" and duration is None:
            raise ValueError("An active timed effect needs a duration")
        return await self.update(
            light_id,
            LightUpdate(
                on=OnState(on=True),
                timed_effects=TimedEffectsState(
                    effect=effect,
                    duration=None
                    if duration is None
                    else _transition_to_milliseconds(duration),
                ),
            ),
        )

    async def stop_timed_effect(
        self, light_id: ResourceId
    ) -> HueApiResponse[ResourceIdentifier]:
        return await self.update(
            light_id, LightUpdate(timed_effects=TimedEffectsState(effect="no_effect"))
        )

    async def set_powerup_preset(
        self,
        light_id: ResourceId,
        preset: Literal["safety", "powerfail", "last_on_state"],
    ) -> HueApiResponse[ResourceIdentifier]:
        if preset not in {"safety", "powerfail", "last_on_state"}:
            raise ValueError("Use LightUpdate(powerup=...) for a custom preset")
        return await self.update(
            light_id, LightUpdate(powerup=PowerupState(preset=preset))
        )
