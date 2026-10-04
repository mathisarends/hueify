from enum import StrEnum
from typing import Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class HueModel(BaseModel):
    """Base for Hue payloads that preserves fields added by bridge firmware."""

    model_config = ConfigDict(extra="allow")


class ResourceType(StrEnum):
    LIGHT = "light"
    GROUPED_LIGHT = "grouped_light"
    ROOM = "room"
    ZONE = "zone"
    SCENE = "scene"
    SMART_SCENE = "smart_scene"
    PUBLIC_IMAGE = "public_image"
    DEVICE = "device"
    DEVICE_POWER = "device_power"
    DEVICE_SOFTWARE_UPDATE = "device_software_update"
    BRIDGE = "bridge"
    BRIDGE_HOME = "bridge_home"
    SERVICE_GROUP = "service_group"
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
    AUTH_V1 = "auth_v1"
    SWITCH_INPUT_CONFIGURATION = "switch_input_configuration"

    @classmethod
    def _missing_(cls, value: object) -> Self | None:
        """Retain resource types added by firmware without losing known enums."""
        if not isinstance(value, str):
            return None
        member = str.__new__(cls, value)
        member._name_ = f"UNKNOWN_{value.upper()}"
        member._value_ = value
        return member


class ResourceReference(HueModel):
    rid: UUID
    rtype: ResourceType


class ResourceIdentifier(ResourceReference):
    pass


class HueApiError(HueModel):
    description: str


class HueApiResponse[T: BaseModel](HueModel):
    errors: list[HueApiError] = Field(default_factory=list)
    data: list[T] = Field(default_factory=list)


class NamedMetadata(HueModel):
    name: str


class HueResource(HueModel):
    """A CLIP resource, including resource types from newer firmware."""

    id: UUID
    type: ResourceType
    id_v1: str | None = None


class NamedResource(HueModel):
    """Base for resources that carry a stable ID and a user-visible name."""

    id: UUID
    metadata: NamedMetadata

    @property
    def name(self) -> str:
        return self.metadata.name
