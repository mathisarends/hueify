"""Partial resource changes and CLIP v2 event envelopes."""

from datetime import datetime
from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import Discriminator, Field, Tag

from hueify.models.base import (
    HueModel,
    ResourceReference,
    ResourceType,
)
from hueify.models.lighting import (
    DimmingEventState,
    EffectsV2State,
    EntertainmentChannel,
    GradientState,
    GroupedLight,
    GroupUpdate,
    LightUpdate,
    SceneStatus,
    SceneUpdate,
    SignalingState,
    StreamingStatus,
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
    MetadataUpdate,
    Motion,
    MotionAreaCandidate,
    MotionAreaConfiguration,
    RelativeRotary,
    SecurityAreaMotion,
    ServiceGroup,
    SmartScene,
    SmartSceneDay,
    Speaker,
    SwitchInputConfiguration,
    Tamper,
    TamperReport,
    Temperature,
    WifiConnectivity,
    ZgpConnectivity,
    ZigbeeConnectivity,
    ZigbeeDeviceDiscovery,
)


class HueEvent(HueModel):
    id: UUID
    type: ResourceType


class LightEvent(LightUpdate, HueEvent):
    type: Literal[ResourceType.LIGHT] = ResourceType.LIGHT
    id_v1: str | None = None
    owner: ResourceReference | None = None
    dimming: DimmingEventState | None = None
    gradient: GradientState | None = None
    effects_v2: EffectsV2State | None = None
    signaling: SignalingState | None = None


class RoomEvent(GroupUpdate, HueEvent):
    type: Literal[ResourceType.ROOM] = ResourceType.ROOM
    services: list[ResourceReference] | None = None


class ZoneEvent(GroupUpdate, HueEvent):
    type: Literal[ResourceType.ZONE] = ResourceType.ZONE
    services: list[ResourceReference] | None = None


class SceneEvent(SceneUpdate, HueEvent):
    type: Literal[ResourceType.SCENE] = ResourceType.SCENE
    status: SceneStatus | None = None


class EntertainmentConfigurationEvent(HueEvent):
    """Reports that an area started or stopped streaming, and who owns it.

    An area another application takes over arrives here, which is the only
    notice a streaming session gets that the bridge stopped listening to it.
    """

    type: Literal[ResourceType.ENTERTAINMENT_CONFIGURATION] = (
        ResourceType.ENTERTAINMENT_CONFIGURATION
    )
    status: StreamingStatus | str | None = None
    active_streamer: ResourceReference | None = None
    channels: list[EntertainmentChannel] | None = None

    @property
    def is_streaming(self) -> bool:
        return self.status == StreamingStatus.ACTIVE


class DeviceEvent(Device, HueEvent):
    services: list[ResourceReference] | None = None


class DevicePowerEvent(DevicePower, HueEvent):
    pass


class DeviceSoftwareUpdateEvent(DeviceSoftwareUpdate, HueEvent):
    problems: list[str] | None = None


class BridgeEvent(Bridge, HueEvent):
    pass


class BridgeHomeEvent(BridgeHome, HueEvent):
    children: list[ResourceReference] | None = None
    services: list[ResourceReference] | None = None


class ServiceGroupEvent(ServiceGroup, HueEvent):
    services: list[ResourceReference] | None = None


class MotionEvent(Motion, HueEvent):
    pass


class CameraMotionEvent(CameraMotion, HueEvent):
    pass


class TemperatureEvent(Temperature, HueEvent):
    pass


class LightLevelEvent(LightLevel, HueEvent):
    pass


class ButtonEvent(Button, HueEvent):
    pass


class BellButtonEvent(BellButton, HueEvent):
    pass


class RelativeRotaryEvent(RelativeRotary, HueEvent):
    pass


class ContactEvent(Contact, HueEvent):
    pass


class TamperEvent(Tamper, HueEvent):
    tamper_reports: list[TamperReport] | None = None


class GroupedMotionEvent(GroupedMotion, HueEvent):
    pass


class GroupedLightLevelEvent(GroupedLightLevel, HueEvent):
    pass


class ZigbeeConnectivityEvent(ZigbeeConnectivity, HueEvent):
    pass


class ZgpConnectivityEvent(ZgpConnectivity, HueEvent):
    pass


class WifiConnectivityEvent(WifiConnectivity, HueEvent):
    pass


class ZigbeeDeviceDiscoveryEvent(ZigbeeDeviceDiscovery, HueEvent):
    pass


class EntertainmentEvent(Entertainment, HueEvent):
    pass


class SpeakerEvent(Speaker, HueEvent):
    alerts: list[str] | None = None


class BehaviorScriptEvent(BehaviorScript, HueEvent):
    pass


class BehaviorInstanceEvent(BehaviorInstance, HueEvent):
    dependees: list[ResourceReference] | None = None


class GeofenceClientEvent(GeofenceClient, HueEvent):
    pass


class GeolocationEvent(Geolocation, HueEvent):
    pass


class HomekitEvent(Homekit, HueEvent):
    pass


class MatterEvent(Matter, HueEvent):
    pass


class MatterFabricEvent(MatterFabric, HueEvent):
    pass


class ConvenienceAreaMotionEvent(ConvenienceAreaMotion, HueEvent):
    pass


class SecurityAreaMotionEvent(SecurityAreaMotion, HueEvent):
    pass


class MotionAreaCandidateEvent(MotionAreaCandidate, HueEvent):
    motion_sensors: list[ResourceReference] | None = None


class MotionAreaConfigurationEvent(MotionAreaConfiguration, HueEvent):
    motion_sensors: list[ResourceReference] | None = None


class SwitchInputConfigurationEvent(SwitchInputConfiguration, HueEvent):
    pass


class SmartSceneEvent(SmartScene, HueEvent):
    metadata: MetadataUpdate | None = None
    group: ResourceReference | None = None
    week_timeslots: list[SmartSceneDay] | None = None


class GroupedLightEvent(GroupedLight, HueEvent):
    dimming: DimmingEventState | None = None


_UNTYPED_EVENT = "other"
_TYPED_EVENTS = frozenset(
    {
        "light",
        "room",
        "zone",
        "scene",
        "entertainment_configuration",
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
        "smart_scene",
        "grouped_light",
    }
)


def _event_tag(value: Any) -> str:
    resource_type = (
        value.get("type") if isinstance(value, dict) else getattr(value, "type", None)
    )
    tag = str(resource_type)
    return tag if tag in _TYPED_EVENTS else _UNTYPED_EVENT


# Resource types hueify models explicitly are parsed into their own event; every
# other type the bridge reports stays a plain HueEvent instead of failing.
AnyHueEvent = Annotated[
    Annotated[LightEvent, Tag("light")]
    | Annotated[RoomEvent, Tag("room")]
    | Annotated[ZoneEvent, Tag("zone")]
    | Annotated[SceneEvent, Tag("scene")]
    | Annotated[EntertainmentConfigurationEvent, Tag("entertainment_configuration")]
    | Annotated[DeviceEvent, Tag("device")]
    | Annotated[DevicePowerEvent, Tag("device_power")]
    | Annotated[DeviceSoftwareUpdateEvent, Tag("device_software_update")]
    | Annotated[BridgeEvent, Tag("bridge")]
    | Annotated[BridgeHomeEvent, Tag("bridge_home")]
    | Annotated[ServiceGroupEvent, Tag("service_group")]
    | Annotated[MotionEvent, Tag("motion")]
    | Annotated[CameraMotionEvent, Tag("camera_motion")]
    | Annotated[TemperatureEvent, Tag("temperature")]
    | Annotated[LightLevelEvent, Tag("light_level")]
    | Annotated[ButtonEvent, Tag("button")]
    | Annotated[BellButtonEvent, Tag("bell_button")]
    | Annotated[RelativeRotaryEvent, Tag("relative_rotary")]
    | Annotated[ContactEvent, Tag("contact")]
    | Annotated[TamperEvent, Tag("tamper")]
    | Annotated[GroupedMotionEvent, Tag("grouped_motion")]
    | Annotated[GroupedLightLevelEvent, Tag("grouped_light_level")]
    | Annotated[ZigbeeConnectivityEvent, Tag("zigbee_connectivity")]
    | Annotated[ZgpConnectivityEvent, Tag("zgp_connectivity")]
    | Annotated[WifiConnectivityEvent, Tag("wifi_connectivity")]
    | Annotated[ZigbeeDeviceDiscoveryEvent, Tag("zigbee_device_discovery")]
    | Annotated[EntertainmentEvent, Tag("entertainment")]
    | Annotated[SpeakerEvent, Tag("speaker")]
    | Annotated[BehaviorScriptEvent, Tag("behavior_script")]
    | Annotated[BehaviorInstanceEvent, Tag("behavior_instance")]
    | Annotated[GeofenceClientEvent, Tag("geofence_client")]
    | Annotated[GeolocationEvent, Tag("geolocation")]
    | Annotated[HomekitEvent, Tag("homekit")]
    | Annotated[MatterEvent, Tag("matter")]
    | Annotated[MatterFabricEvent, Tag("matter_fabric")]
    | Annotated[ConvenienceAreaMotionEvent, Tag("convenience_area_motion")]
    | Annotated[SecurityAreaMotionEvent, Tag("security_area_motion")]
    | Annotated[MotionAreaCandidateEvent, Tag("motion_area_candidate")]
    | Annotated[MotionAreaConfigurationEvent, Tag("motion_area_configuration")]
    | Annotated[SwitchInputConfigurationEvent, Tag("switch_input_configuration")]
    | Annotated[SmartSceneEvent, Tag("smart_scene")]
    | Annotated[GroupedLightEvent, Tag("grouped_light")]
    | Annotated[HueEvent, Tag(_UNTYPED_EVENT)],
    Discriminator(_event_tag),
]


class HueEventMessage(HueModel):
    """One container of an event stream payload, holding the changed resources."""

    data: list[AnyHueEvent] = Field(default_factory=list)
    creationtime: datetime | None = None
