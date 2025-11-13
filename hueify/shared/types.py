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

    PUBLIC_IMAGE = "public_image"

    ENTERTAINMENT = "entertainment"
    ENTERTAINMENT_CONFIGURATION = "entertainment_configuration"
    BUTTON = "button"
    TEMPERATURE = "temperature"
    LIGHT_LEVEL = "light_level"
    MOTION = "motion"


class ResourceReference(BaseModel):
    rid: UUID
    rtype: ResourceType


class LightOnState(BaseModel):
    on: bool
