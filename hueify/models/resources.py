"""Typed mixed-resource responses from the CLIP v2 inventory endpoint."""

from typing import Annotated, Any

from pydantic import Discriminator, Tag

from hueify.models.base import HueResource
from hueify.models.lighting import (
    EntertainmentConfiguration,
    GroupedLight,
    Light,
    Room,
    Scene,
    Zone,
)
from hueify.models.services import (
    BehaviorInstance,
    BehaviorScript,
    BellButton,
    Bridge,
    BridgeHome,
    Button,
    CameraMotion,
    Contact,
    ConvenienceAreaMotion,
    Device,
    DevicePower,
    DeviceSoftwareUpdate,
    Entertainment,
    GeofenceClient,
    Geolocation,
    GroupedLightLevel,
    GroupedMotion,
    Homekit,
    LightLevel,
    Matter,
    MatterFabric,
    Motion,
    MotionAreaCandidate,
    MotionAreaConfiguration,
    RelativeRotary,
    SecurityAreaMotion,
    ServiceGroup,
    SmartScene,
    Speaker,
    SwitchInputConfiguration,
    Tamper,
    Temperature,
    WifiConnectivity,
    ZgpConnectivity,
    ZigbeeConnectivity,
    ZigbeeDeviceDiscovery,
)


def _resource_tag(value: Any) -> str:
    kind = (
        value.get("type") if isinstance(value, dict) else getattr(value, "type", None)
    )
    tag = str(kind)
    return tag if tag in _RESOURCE_TYPES else "other"


_RESOURCE_TYPES = frozenset(
    {
        "light",
        "grouped_light",
        "room",
        "zone",
        "scene",
        "smart_scene",
        "device",
        "device_power",
        "device_software_update",
        "bridge",
        "bridge_home",
        "service_group",
        "motion",
        "camera_motion",
        "temperature",
        "light_level",
        "button",
        "bell_button",
        "relative_rotary",
        "contact",
        "tamper",
        "grouped_motion",
        "grouped_light_level",
        "zigbee_connectivity",
        "zgp_connectivity",
        "wifi_connectivity",
        "zigbee_device_discovery",
        "entertainment",
        "entertainment_configuration",
        "speaker",
        "behavior_script",
        "behavior_instance",
        "geofence_client",
        "geolocation",
        "homekit",
        "matter",
        "matter_fabric",
        "convenience_area_motion",
        "security_area_motion",
        "motion_area_candidate",
        "motion_area_configuration",
        "switch_input_configuration",
    }
)


AnyHueResource = Annotated[
    Annotated[Light, Tag("light")]
    | Annotated[GroupedLight, Tag("grouped_light")]
    | Annotated[Room, Tag("room")]
    | Annotated[Zone, Tag("zone")]
    | Annotated[Scene, Tag("scene")]
    | Annotated[SmartScene, Tag("smart_scene")]
    | Annotated[Device, Tag("device")]
    | Annotated[DevicePower, Tag("device_power")]
    | Annotated[DeviceSoftwareUpdate, Tag("device_software_update")]
    | Annotated[Bridge, Tag("bridge")]
    | Annotated[BridgeHome, Tag("bridge_home")]
    | Annotated[ServiceGroup, Tag("service_group")]
    | Annotated[Motion, Tag("motion")]
    | Annotated[CameraMotion, Tag("camera_motion")]
    | Annotated[Temperature, Tag("temperature")]
    | Annotated[LightLevel, Tag("light_level")]
    | Annotated[Button, Tag("button")]
    | Annotated[BellButton, Tag("bell_button")]
    | Annotated[RelativeRotary, Tag("relative_rotary")]
    | Annotated[Contact, Tag("contact")]
    | Annotated[Tamper, Tag("tamper")]
    | Annotated[GroupedMotion, Tag("grouped_motion")]
    | Annotated[GroupedLightLevel, Tag("grouped_light_level")]
    | Annotated[ZigbeeConnectivity, Tag("zigbee_connectivity")]
    | Annotated[ZgpConnectivity, Tag("zgp_connectivity")]
    | Annotated[WifiConnectivity, Tag("wifi_connectivity")]
    | Annotated[ZigbeeDeviceDiscovery, Tag("zigbee_device_discovery")]
    | Annotated[Entertainment, Tag("entertainment")]
    | Annotated[EntertainmentConfiguration, Tag("entertainment_configuration")]
    | Annotated[Speaker, Tag("speaker")]
    | Annotated[BehaviorScript, Tag("behavior_script")]
    | Annotated[BehaviorInstance, Tag("behavior_instance")]
    | Annotated[GeofenceClient, Tag("geofence_client")]
    | Annotated[Geolocation, Tag("geolocation")]
    | Annotated[Homekit, Tag("homekit")]
    | Annotated[Matter, Tag("matter")]
    | Annotated[MatterFabric, Tag("matter_fabric")]
    | Annotated[ConvenienceAreaMotion, Tag("convenience_area_motion")]
    | Annotated[SecurityAreaMotion, Tag("security_area_motion")]
    | Annotated[MotionAreaCandidate, Tag("motion_area_candidate")]
    | Annotated[MotionAreaConfiguration, Tag("motion_area_configuration")]
    | Annotated[SwitchInputConfiguration, Tag("switch_input_configuration")]
    | Annotated[HueResource, Tag("other")],
    Discriminator(_resource_tag),
]
