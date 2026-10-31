"""Partial resource changes, separate from snapshots and writable requests."""

from datetime import datetime
from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import Discriminator, Field, Tag

from hueify.models.base import (
    HueModel,
    HueResource,
    MetadataUpdate,
    ResourceReference,
    ResourceType,
)
from hueify.models.lighting import (
    AlertState,
    ColorState,
    ColorTemperatureDelta,
    ColorTemperatureState,
    DimmingDelta,
    DimmingEventState,
    DynamicsState,
    EffectsState,
    EffectsV2State,
    EntertainmentChannel,
    EntertainmentConfigurationType,
    EntertainmentLocations,
    GradientEventState,
    GroupMetadataUpdate,
    LightMetadataUpdate,
    LightStateMixin,
    OnState,
    PowerupEventState,
    SceneActionTarget,
    SceneMetadataUpdate,
    ScenePalette,
    SceneStatus,
    SignalingState,
    StreamingStatus,
    StreamProxy,
    TimedEffectsState,
)
from hueify.models.services import (
    BellState,
    ButtonState,
    ContactReport,
    ControlMetadata,
    EntertainmentSegments,
    LightLevelState,
    LightLevelStateMixin,
    MatterFabricData,
    MotionSensitivity,
    MotionState,
    MotionStateMixin,
    NamedServiceMixin,
    PowerState,
    ProductData,
    RelativeRotaryState,
    SmartSceneActiveTimeslot,
    SmartSceneDay,
    TamperReport,
    TemperatureState,
    TemperatureStateMixin,
    TimeZone,
    UserTest,
    WifiSignalStrength,
    ZigbeeChannel,
)


class HueEvent(HueResource):
    """A partial resource change, with its envelope action and timestamp."""

    operation: str | None = None
    creationtime: datetime | None = None


class _OwnedEvent(HueEvent):
    owner: ResourceReference | None = None


class LightEvent(_OwnedEvent, LightStateMixin):
    type: Literal[ResourceType.LIGHT] = ResourceType.LIGHT
    metadata: LightMetadataUpdate | None = None
    on: OnState | None = None
    dimming: DimmingEventState | None = None
    dimming_delta: DimmingDelta | None = None
    color_temperature: ColorTemperatureState | None = None
    color_temperature_delta: ColorTemperatureDelta | None = None
    color: ColorState | None = None
    gradient: GradientEventState | None = None
    effects: EffectsState | None = None
    effects_v2: EffectsV2State | None = None
    timed_effects: TimedEffectsState | None = None
    dynamics: DynamicsState | None = None
    alert: AlertState | None = None
    signaling: SignalingState | None = None
    powerup: PowerupEventState | None = None
    identify: HueModel | None = None
    service_id: int | None = None
    mode: str | None = None


class _GroupEvent(HueEvent):
    metadata: GroupMetadataUpdate | None = None
    children: list[ResourceReference] | None = None
    services: list[ResourceReference] | None = None


class RoomEvent(_GroupEvent):
    type: Literal[ResourceType.ROOM] = ResourceType.ROOM


class ZoneEvent(_GroupEvent):
    type: Literal[ResourceType.ZONE] = ResourceType.ZONE


class SceneEvent(HueEvent):
    type: Literal[ResourceType.SCENE] = ResourceType.SCENE
    metadata: SceneMetadataUpdate | None = None
    group: ResourceReference | None = None
    actions: list[SceneActionTarget] | None = None
    palette: ScenePalette | None = None
    speed: float | None = Field(default=None, ge=0, le=1)
    auto_dynamic: bool | None = None
    status: SceneStatus | None = None


class EntertainmentConfigurationEvent(HueEvent):
    """Partial area state, including streaming status and ownership changes."""

    type: Literal[ResourceType.ENTERTAINMENT_CONFIGURATION] = (
        ResourceType.ENTERTAINMENT_CONFIGURATION
    )
    metadata: MetadataUpdate | None = None
    configuration_type: EntertainmentConfigurationType | None = None
    status: StreamingStatus | str | None = None
    active_streamer: ResourceReference | None = None
    channels: list[EntertainmentChannel] | None = None
    locations: EntertainmentLocations | None = None
    stream_proxy: StreamProxy | None = None

    @property
    def is_streaming(self) -> bool:
        return self.status == StreamingStatus.ACTIVE


class DeviceEvent(_OwnedEvent, NamedServiceMixin):
    type: Literal[ResourceType.DEVICE] = ResourceType.DEVICE
    metadata: MetadataUpdate | None = None
    product_data: ProductData | None = None
    services: list[ResourceReference] | None = None
    identify: HueModel | None = None
    usertest: UserTest | None = None


class DevicePowerEvent(_OwnedEvent):
    type: Literal[ResourceType.DEVICE_POWER] = ResourceType.DEVICE_POWER
    power_state: PowerState | None = None


class DeviceSoftwareUpdateEvent(_OwnedEvent):
    type: Literal[ResourceType.DEVICE_SOFTWARE_UPDATE] = (
        ResourceType.DEVICE_SOFTWARE_UPDATE
    )
    state: str | None = None
    problems: list[str] | None = None


class BridgeEvent(_OwnedEvent):
    type: Literal[ResourceType.BRIDGE] = ResourceType.BRIDGE
    bridge_id: str | None = None
    time_zone: TimeZone | None = None


class BridgeHomeEvent(HueEvent):
    type: Literal[ResourceType.BRIDGE_HOME] = ResourceType.BRIDGE_HOME
    children: list[ResourceReference] | None = None
    services: list[ResourceReference] | None = None


class ServiceGroupEvent(HueEvent):
    type: Literal[ResourceType.SERVICE_GROUP] = ResourceType.SERVICE_GROUP
    services: list[ResourceReference] | None = None


class _MotionEvent(_OwnedEvent, MotionStateMixin):
    enabled: bool | None = None
    motion: MotionState | None = None


class MotionEvent(_MotionEvent):
    type: Literal[ResourceType.MOTION] = ResourceType.MOTION
    sensitivity: MotionSensitivity | None = None


class CameraMotionEvent(_MotionEvent):
    type: Literal[ResourceType.CAMERA_MOTION] = ResourceType.CAMERA_MOTION


class TemperatureEvent(_OwnedEvent, TemperatureStateMixin):
    type: Literal[ResourceType.TEMPERATURE] = ResourceType.TEMPERATURE
    enabled: bool | None = None
    temperature: TemperatureState | None = None


class LightLevelEvent(_OwnedEvent, LightLevelStateMixin):
    type: Literal[ResourceType.LIGHT_LEVEL] = ResourceType.LIGHT_LEVEL
    enabled: bool | None = None
    light: LightLevelState | None = None


class ButtonEvent(_OwnedEvent):
    type: Literal[ResourceType.BUTTON] = ResourceType.BUTTON
    metadata: ControlMetadata | None = None
    button: ButtonState | None = None


class BellButtonEvent(_OwnedEvent):
    type: Literal[ResourceType.BELL_BUTTON] = ResourceType.BELL_BUTTON
    metadata: ControlMetadata | None = None
    bell: BellState | None = None


class RelativeRotaryEvent(_OwnedEvent):
    type: Literal[ResourceType.RELATIVE_ROTARY] = ResourceType.RELATIVE_ROTARY
    metadata: ControlMetadata | None = None
    relative_rotary: RelativeRotaryState | None = None


class ContactEvent(_OwnedEvent):
    type: Literal[ResourceType.CONTACT] = ResourceType.CONTACT
    enabled: bool | None = None
    contact_report: ContactReport | None = None


class TamperEvent(_OwnedEvent):
    type: Literal[ResourceType.TAMPER] = ResourceType.TAMPER
    tamper_reports: list[TamperReport] | None = None


class GroupedMotionEvent(_OwnedEvent, MotionStateMixin):
    type: Literal[ResourceType.GROUPED_MOTION] = ResourceType.GROUPED_MOTION
    motion: MotionState | None = None


class GroupedLightLevelEvent(_OwnedEvent, LightLevelStateMixin):
    type: Literal[ResourceType.GROUPED_LIGHT_LEVEL] = ResourceType.GROUPED_LIGHT_LEVEL
    light: LightLevelState | None = None


class ZigbeeConnectivityEvent(_OwnedEvent):
    type: Literal[ResourceType.ZIGBEE_CONNECTIVITY] = ResourceType.ZIGBEE_CONNECTIVITY
    status: str | None = None
    mac_address: str | None = None
    channel: ZigbeeChannel | None = None
    extended_pan_id: str | None = None


class ZgpConnectivityEvent(_OwnedEvent):
    type: Literal[ResourceType.ZGP_CONNECTIVITY] = ResourceType.ZGP_CONNECTIVITY
    status: str | None = None
    source_id: str | None = None


class WifiConnectivityEvent(_OwnedEvent):
    type: Literal[ResourceType.WIFI_CONNECTIVITY] = ResourceType.WIFI_CONNECTIVITY
    status: str | None = None
    mac_address: str | None = None
    signal_strength: WifiSignalStrength | None = None


class ZigbeeDeviceDiscoveryEvent(_OwnedEvent):
    type: Literal[ResourceType.ZIGBEE_DEVICE_DISCOVERY] = (
        ResourceType.ZIGBEE_DEVICE_DISCOVERY
    )
    status: str | None = None


class EntertainmentEvent(_OwnedEvent):
    type: Literal[ResourceType.ENTERTAINMENT] = ResourceType.ENTERTAINMENT
    renderer: bool | None = None
    proxy: bool | None = None
    max_streams: int | None = None
    segments: EntertainmentSegments | None = None


class SpeakerEvent(_OwnedEvent):
    type: Literal[ResourceType.SPEAKER] = ResourceType.SPEAKER
    alerts: list[str] | None = None


class BehaviorScriptEvent(HueEvent, NamedServiceMixin):
    type: Literal[ResourceType.BEHAVIOR_SCRIPT] = ResourceType.BEHAVIOR_SCRIPT
    description: str | None = None
    configuration_schema: dict[str, Any] | None = None
    trigger_schema: dict[str, Any] | None = None
    state_schema: dict[str, Any] | None = None
    version: str | None = None
    metadata: MetadataUpdate | None = None


class BehaviorInstanceEvent(HueEvent, NamedServiceMixin):
    type: Literal[ResourceType.BEHAVIOR_INSTANCE] = ResourceType.BEHAVIOR_INSTANCE
    script_id: UUID | None = None
    enabled: bool | None = None
    state: dict[str, Any] | None = None
    configuration: dict[str, Any] | None = None
    dependees: list[ResourceReference] | None = None
    status: str | None = None
    last_error: str | None = None
    metadata: MetadataUpdate | None = None


class GeofenceClientEvent(HueEvent):
    type: Literal[ResourceType.GEOFENCE_CLIENT] = ResourceType.GEOFENCE_CLIENT
    name: str | None = None
    is_at_home: bool | None = None


class GeolocationEvent(HueEvent):
    type: Literal[ResourceType.GEOLOCATION] = ResourceType.GEOLOCATION
    is_configured: bool | None = None


class HomekitEvent(_OwnedEvent):
    type: Literal[ResourceType.HOMEKIT] = ResourceType.HOMEKIT
    status: str | None = None
    action: str | None = None


class MatterEvent(_OwnedEvent):
    type: Literal[ResourceType.MATTER] = ResourceType.MATTER
    has_qr_code: bool | None = None
    max_fabrics: int | None = None


class MatterFabricEvent(_OwnedEvent):
    type: Literal[ResourceType.MATTER_FABRIC] = ResourceType.MATTER_FABRIC
    status: str | None = None
    fabric_data: MatterFabricData | None = None
    creation_time: datetime | None = None


class ConvenienceAreaMotionEvent(_MotionEvent):
    type: Literal[ResourceType.CONVENIENCE_AREA_MOTION] = (
        ResourceType.CONVENIENCE_AREA_MOTION
    )


class SecurityAreaMotionEvent(_MotionEvent):
    type: Literal[ResourceType.SECURITY_AREA_MOTION] = ResourceType.SECURITY_AREA_MOTION


class MotionAreaCandidateEvent(_OwnedEvent):
    type: Literal[ResourceType.MOTION_AREA_CANDIDATE] = (
        ResourceType.MOTION_AREA_CANDIDATE
    )
    motion_sensors: list[ResourceReference] | None = None


class MotionAreaConfigurationEvent(_OwnedEvent):
    type: Literal[ResourceType.MOTION_AREA_CONFIGURATION] = (
        ResourceType.MOTION_AREA_CONFIGURATION
    )
    enabled: bool | None = None
    motion_sensors: list[ResourceReference] | None = None


class SwitchInputConfigurationEvent(_OwnedEvent):
    type: Literal[ResourceType.SWITCH_INPUT_CONFIGURATION] = (
        ResourceType.SWITCH_INPUT_CONFIGURATION
    )
    switch_mode: str | HueModel | None = None


class SmartSceneEvent(HueEvent):
    type: Literal[ResourceType.SMART_SCENE] = ResourceType.SMART_SCENE
    metadata: MetadataUpdate | None = None
    group: ResourceReference | None = None
    week_timeslots: list[SmartSceneDay] | None = None
    transition_duration: int | None = Field(default=None, ge=0)
    active_timeslot: SmartSceneActiveTimeslot | None = None
    state: str | None = None

    @property
    def name(self) -> str | None:
        return self.metadata.name if self.metadata else None


class GroupedLightEvent(_OwnedEvent, LightStateMixin):
    type: Literal[ResourceType.GROUPED_LIGHT] = ResourceType.GROUPED_LIGHT
    on: OnState | None = None
    dimming: DimmingEventState | None = None
    color_temperature: ColorTemperatureState | None = None
    color: ColorState | None = None
    dynamics: DynamicsState | None = None
    alert: AlertState | None = None
    signaling: SignalingState | None = None


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
    type: str | None = None
    creationtime: datetime | None = None
