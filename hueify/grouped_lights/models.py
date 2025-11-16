from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from hueify.shared.resource.models import (
    ColorTemperatureState,
    LightOnState,
    ResourceType,
)
from hueify.sse.models import DimmingState


class GroupedLightState(BaseModel):
    id: UUID | None = None
    type: Literal[ResourceType.GROUPED_LIGHT] = ResourceType.GROUPED_LIGHT
    on: LightOnState
    dimming: DimmingState | None = None
    color_temperature: ColorTemperatureState | None = None
