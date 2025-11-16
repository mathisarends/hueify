from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field


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
    RELATIVE_ROTARY = "relative_rotary"


class ResourceReference(BaseModel):
    rid: UUID
    rtype: ResourceType


class LightOnState(BaseModel):
    on: bool


class DimmingState(BaseModel):
    brightness: float = Field(ge=0, le=100)


class ColorTemperatureState(BaseModel):
    mirek: int | None = Field(default=None, ge=153, le=500)
    mirek_valid: bool | None = None


class ResourceMetadata(BaseModel):
    name: str


class ResourceInfo(BaseModel):
    id: UUID
    metadata: ResourceMetadata
