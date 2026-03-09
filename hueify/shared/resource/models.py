from enum import StrEnum
from typing import Any, TypeVar
from uuid import UUID

from pydantic import BaseModel, Field


class ResourceType(StrEnum):
    LIGHT = "light"
    GROUPED_LIGHT = "grouped_light"
    ROOM = "room"
    ZONE = "zone"
    BRIDGE_HOME = "bridge_home"
    SCENE = "scene"
    SMART_SCENE = "smart_scene"
    PUBLIC_IMAGE = "public_image"
    MOTION = "motion"
    CAMERA_MOTION = "camera_motion"
    TEMPERATURE = "temperature"
    LIGHT_LEVEL = "light_level"
    BUTTON = "button"
    BELL_BUTTON = "bell_button"
    RELATIVE_ROTARY = "relative_rotary"
    CONTACT = "contact"
    TAMPER = "tamper"
    GROUPED_MOTION = "grouped_motion"
    GROUPED_LIGHT_LEVEL = "grouped_light_level"
    DEVICE = "device"
    DEVICE_POWER = "device_power"
    DEVICE_SOFTWARE_UPDATE = "device_software_update"
    BRIDGE = "bridge"
    SERVICE_GROUP = "service_group"
    ZIGBEE_CONNECTIVITY = "zigbee_connectivity"
    ZGP_CONNECTIVITY = "zgp_connectivity"
    WIFI_CONNECTIVITY = "wifi_connectivity"
    ZIGBEE_DEVICE_DISCOVERY = "zigbee_device_discovery"
    ENTERTAINMENT = "entertainment"
    ENTERTAINMENT_CONFIGURATION = "entertainment_configuration"
    SPEAKER = "speaker"
    BEHAVIOR_SCRIPT = "behavior_script"
    BEHAVIOR_INSTANCE = "behavior_instance"
    GEOFENCE_CLIENT = "geofence_client"
    GEOLOCATION = "geolocation"
    HOMEKIT = "homekit"
    MATTER = "matter"
    MATTER_FABRIC = "matter_fabric"
    CONVENIENCE_AREA_MOTION = "convenience_area_motion"
    SECURITY_AREA_MOTION = "security_area_motion"
    MOTION_AREA_CANDIDATE = "motion_area_candidate"
    MOTION_AREA_CONFIGURATION = "motion_area_configuration"


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
    type: ResourceType


class ActionResult(BaseModel):
    """Outcome returned by every command method on lights, rooms, and zones.

    Attributes:
        message: Human-readable description of what happened.
        success: ``True`` when the command completed without errors.
        clamped: ``True`` when an input value was silently clamped to its
            valid range (e.g. brightness > 100 → 100).
        final_value: The effective value that was actually applied, present
            only when the command accepted a numeric parameter.
    """

    message: str
    success: bool = True
    clamped: bool = False
    final_value: Any | None = None


class ControllableLight(BaseModel):
    id: UUID
    on: LightOnState
    dimming: DimmingState | None
    color_temperature: ColorTemperatureState | None


class ControllableLightUpdate(BaseModel):
    on: LightOnState | None = None
    dimming: DimmingState | None = None
    color_temperature: ColorTemperatureState | None = None


TLightInfo = TypeVar("TLightInfo", bound=ControllableLight)
