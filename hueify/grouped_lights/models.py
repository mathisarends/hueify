from typing import Literal
from uuid import UUID

from pydantic import TypeAdapter

from hueify.shared.resource.models import (
    ControllableLight,
    ResourceInfo,
    ResourceType,
)


class GroupedLightState(ControllableLight):
    type: Literal[ResourceType.GROUPED_LIGHT] = ResourceType.GROUPED_LIGHT


class GroupedLightInfo(ResourceInfo):
    type: Literal[ResourceType.GROUPED_LIGHT] = ResourceType.GROUPED_LIGHT
    owner: dict[str, UUID] | None = None


GroupedLightInfoListAdapter = TypeAdapter(list[GroupedLightInfo])
