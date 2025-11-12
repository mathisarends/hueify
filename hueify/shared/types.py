from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel


class ResourceType(StrEnum):
    LIGHT = "light"
    SCENE = "scene"
    ROOM = "room"
    ZONE = "zone"
    BRIDGE_HOME = "bridge_home"
    GROUPED_LIGHT = "grouped_light"
    DEVICE = "device"
    BRIDGE = "bridge"


class ResourceReference(BaseModel):
    rid: UUID
    rtype: ResourceType


class LightOnState(BaseModel):
    on: bool
