from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

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


class GroupType(StrEnum):
    ROOM = "room"
    ZONE = "zone"

    DEVICE_SOFTWARE_UPDATE = "device_software_update"
    DEVICE_POWER = "device_power"

    ZIGBEE_CONNECTIVITY = "zigbee_connectivity"
    ZGP_CONNECTIVITY = "zgp_connectivity"
    ZIGBEE_DEVICE_DISCOVERY = "zigbee_device_discovery"
    WIFI_CONNECTIVITY = "wifi_connectivity"

    MOTION = "motion"
    CAMERA_MOTION = "camera_motion"
    TEMPERATURE = "temperature"
    LIGHT_LEVEL = "light_level"
    CONTACT = "contact"
    TAMPER = "tamper"

    BUTTON = "button"
    BELL_BUTTON = "bell_button"
    RELATIVE_ROTARY = "relative_rotary"

    SERVICE_GROUP = "service_group"
    GROUPED_MOTION = "grouped_motion"
    GROUPED_LIGHT_LEVEL = "grouped_light_level"

    BEHAVIOR_SCRIPT = "behavior_script"
    BEHAVIOR_INSTANCE = "behavior_instance"
    SMART_SCENE = "smart_scene"

    GEOFENCE_CLIENT = "geofence_client"
    GEOLOCATION = "geolocation"
    ENTERTAINMENT_CONFIGURATION = "entertainment_configuration"
    ENTERTAINMENT = "entertainment"

    MOTION_AREA_CONFIGURATION = "motion_area_configuration"
    MOTION_AREA_CANDIDATE = "motion_area_candidate"
    CONVENIENCE_AREA_MOTION = "convenience_area_motion"
    SECURITY_AREA_MOTION = "security_area_motion"

    HOMEKIT = "homekit"
    MATTER = "matter"
    MATTER_FABRIC = "matter_fabric"

    SPEAKER = "speaker"
    CLIP = "clip"


class GroupArchetype(StrEnum):
    LIVING_ROOM = "living_room"
    KITCHEN = "kitchen"
    DINING = "dining"
    BEDROOM = "bedroom"
    KIDS_BEDROOM = "kids_bedroom"
    BATHROOM = "bathroom"
    NURSERY = "nursery"
    RECREATION = "recreation"
    OFFICE = "office"
    GYM = "gym"
    HALLWAY = "hallway"
    TOILET = "toilet"
    FRONT_DOOR = "front_door"
    GARAGE = "garage"
    TERRACE = "terrace"
    GARDEN = "garden"
    DRIVEWAY = "driveway"
    CARPORT = "carport"
    HOME = "home"
    DOWNSTAIRS = "downstairs"
    UPSTAIRS = "upstairs"
    TOP_FLOOR = "top_floor"
    ATTIC = "attic"
    GUEST_ROOM = "guest_room"
    STAIRCASE = "staircase"
    LOUNGE = "lounge"
    MAN_CAVE = "man_cave"
    COMPUTER = "computer"
    STUDIO = "studio"
    MUSIC = "music"
    TV = "tv"
    READING = "reading"
    CLOSET = "closet"
    STORAGE = "storage"
    LAUNDRY_ROOM = "laundry_room"
    BALCONY = "balcony"
    PORCH = "porch"
    BARBECUE = "barbecue"
    POOL = "pool"
    OTHER = "other"


class GroupMetadata(BaseModel):
    name: str
    archetype: GroupArchetype


class GroupInfo(BaseModel):
    id: UUID
    type: GroupType
    metadata: GroupMetadata
    children: list[ResourceReference] = Field(default_factory=list)
    services: list[ResourceReference] = Field(default_factory=list)

    @property
    def name(self) -> str:
        return self.metadata.name

    @property
    def archetype(self) -> GroupArchetype:
        return self.metadata.archetype

    def get_grouped_light_reference_if_exists(self) -> UUID | None:
        for service in self.services:
            if service.rtype == ResourceType.GROUPED_LIGHT:
                return service.rid
        return None
