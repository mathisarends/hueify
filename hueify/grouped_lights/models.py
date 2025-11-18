from typing import Literal
from uuid import UUID

from pydantic import BaseModel, TypeAdapter

from hueify.shared.resource.models import (
    ControllableLight,
    ResourceReference,
    ResourceType,
)


class GroupedLightState(ControllableLight):
    type: Literal[ResourceType.GROUPED_LIGHT] = ResourceType.GROUPED_LIGHT


class GroupedLightInfo(BaseModel):
    id: UUID
    type: Literal[ResourceType.GROUPED_LIGHT] = ResourceType.GROUPED_LIGHT
    owner: ResourceReference | None = None
    on: dict[str, bool] | None = None
    dimming: dict[str, float] | None = None

    @property
    def name(self) -> str:
        return f"GroupedLight-{self.id}"


GroupedLightInfoListAdapter = TypeAdapter(list[GroupedLightInfo])
