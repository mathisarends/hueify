from typing import Literal

from hueify.shared.resource.models import (
    ControllableLight,
    ResourceReference,
    ResourceType,
)


class GroupedLightInfo(ControllableLight):
    type: Literal[ResourceType.GROUPED_LIGHT] = ResourceType.GROUPED_LIGHT
    owner: ResourceReference | None = None

    @property
    def name(self) -> str:
        return f"GroupedLight-{self.id}"
