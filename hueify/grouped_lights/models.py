from typing import Literal

from hueify.shared.resource.models import (
    ControllableLight,
    ResourceType,
)


class GroupedLightState(ControllableLight):
    type: Literal[ResourceType.GROUPED_LIGHT] = ResourceType.GROUPED_LIGHT
