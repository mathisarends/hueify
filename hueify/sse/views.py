from enum import StrEnum
from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from hueify.shared.resource.models import ResourceType


class EventType(StrEnum):
    UPDATE = "update"
    ADD = "add"
    DELETE = "delete"


class ButtonEventType(StrEnum):
    INITIAL_PRESS = "initial_press"
    REPEAT = "repeat"
    SHORT_RELEASE = "short_release"
    LONG_PRESS = "long_press"
    LONG_RELEASE = "long_release"
    DOUBLE_SHORT_RELEASE = "double_short_release"


class RotaryAction(StrEnum):
    START = "start"
    REPEAT = "repeat"


class RotaryDirection(StrEnum):
    CLOCK_WISE = "clock_wise"
    COUNTER_CLOCK_WISE = "counter_clock_wise"


class ZigbeeStatus(StrEnum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    CONNECTIVITY_ISSUE = "connectivity_issue"
    UNIDIRECTIONAL_INCOMING = "unidirectional_incoming"


class WifiStatus(StrEnum):
    CONNECTED = "connected"
    NOT_CONNECTED = "not_connected"
    CABLE_CONNECTED = "cable_connected"


class BatteryState(StrEnum):
    NORMAL = "normal"
    LOW = "low"
    CRITICAL = "critical"


class ContactState(StrEnum):
    CONTACT = "contact"
    NO_CONTACT = "no_contact"


class TamperState(StrEnum):
    TAMPERED = "tampered"
    NOT_TAMPERED = "not_tampered"


# ---------------------------------------------------------------------------
# Shared building blocks
# ---------------------------------------------------------------------------


class OwnerReference(BaseModel):
    rid: UUID
    rtype: str


class ResourceReference(BaseModel):
    rid: UUID
    rtype: str


class OnState(BaseModel):
    on: bool


class DimmingState(BaseModel):
    brightness: float


class ColorXY(BaseModel):
    x: float
    y: float


class ColorState(BaseModel):
    xy: ColorXY


class ColorTemperature(BaseModel):
    mirek: int | None = None
    mirek_valid: bool


class ColorTemperatureMirekSchema(BaseModel):
    mirek_minimum: int
    mirek_maximum: int


class GradientPoint(BaseModel):
    color: ColorState


class GradientState(BaseModel):
    points: list[GradientPoint]
    mode: str | None = None
    points_capable: int | None = None
    mode_values: list[str] | None = None
    pixel_count: int | None = None


class EffectsState(BaseModel):
    effect: str | None = None
    status: str | None = None
    status_values: list[str] | None = None
    effect_values: list[str] | None = None


class TimedEffectsState(BaseModel):
    effect: str | None = None
    duration: int | None = None
    status: str | None = None
    status_values: list[str] | None = None
    effect_values: list[str] | None = None


class DynamicsState(BaseModel):
    status: str | None = None
    status_values: list[str] | None = None
    speed: float | None = None
    speed_valid: bool | None = None


class AlertState(BaseModel):
    action_values: list[str] | None = None


class SignalingState(BaseModel):
    status: str | None = None
    signal_values: list[str] | None = None


# ---------------------------------------------------------------------------
# Button / Rotary
# ---------------------------------------------------------------------------


class ButtonReport(BaseModel):
    event: ButtonEventType
    updated: str


class ButtonData(BaseModel):
    button_report: ButtonReport | None = None
    last_event: ButtonEventType | None = None


class RotationData(BaseModel):
    direction: RotaryDirection
    duration: int
    steps: int


class RotaryEvent(BaseModel):
    action: RotaryAction
    rotation: RotationData


class RelativeRotaryData(BaseModel):
    last_event: RotaryEvent | None = None
    rotary_report: RotaryEvent | None = None


# ---------------------------------------------------------------------------
# Sensors
# ---------------------------------------------------------------------------


class MotionData(BaseModel):
    motion: bool | None = None
    motion_valid: bool | None = None


class TemperatureData(BaseModel):
    temperature: float | None = None
    temperature_valid: bool | None = None


class LightLevelData(BaseModel):
    light_level: int | None = None
    light_level_valid: bool | None = None


class ContactReport(BaseModel):
    changed: str
    state: ContactState


class ContactData(BaseModel):
    contact_report: ContactReport | None = None


class TamperReport(BaseModel):
    changed: str
    source: str
    state: TamperState


class TamperData(BaseModel):
    tamper_reports: list[TamperReport] | None = None


# ---------------------------------------------------------------------------
# Connectivity
# ---------------------------------------------------------------------------


class ZigbeeConnectivityData(BaseModel):
    status: ZigbeeStatus | None = None
    mac_address: str | None = None


class ZgpConnectivityData(BaseModel):
    status: ZigbeeStatus | None = None
    source_id: str | None = None


class WifiConnectivityData(BaseModel):
    status: WifiStatus | None = None


# ---------------------------------------------------------------------------
# Device & power
# ---------------------------------------------------------------------------


class DevicePowerData(BaseModel):
    battery_level: int | None = None
    battery_state: BatteryState | None = None


class PowerStateData(BaseModel):
    battery_level: int | None = None
    battery_state: BatteryState | None = None


class DeviceMetadata(BaseModel):
    name: str | None = None
    archetype: str | None = None


class ProductData(BaseModel):
    model_id: str | None = None
    manufacturer_name: str | None = None
    product_name: str | None = None
    product_archetype: str | None = None
    certified: bool | None = None
    software_version: str | None = None
    hardware_platform_type: str | None = None


# ---------------------------------------------------------------------------
# Scenes
# ---------------------------------------------------------------------------


class SceneStatus(BaseModel):
    active: str
    last_recall: str | None = None


class SmartSceneState(BaseModel):
    active_timeslot: dict[str, Any] | None = None
    active_procedure: str | None = None
    last_recall: str | None = None


# ---------------------------------------------------------------------------
# Grouped sensors
# ---------------------------------------------------------------------------


class GroupedMotionData(BaseModel):
    motion: bool | None = None
    motion_valid: bool | None = None


class GroupedLightLevelData(BaseModel):
    light_level: int | None = None
    light_level_valid: bool | None = None


# ---------------------------------------------------------------------------
# Entertainment
# ---------------------------------------------------------------------------


class EntertainmentConfigurationStatus(BaseModel):
    status: str | None = None  # "active" | "inactive"


# ---------------------------------------------------------------------------
# Smart home integrations
# ---------------------------------------------------------------------------


class HomekitData(BaseModel):
    status: str | None = None  # "paired" | "pairing" | "unpaired"


class MatterData(BaseModel):
    has_qr_code: bool | None = None
    max_fabrics: int | None = None


# ---------------------------------------------------------------------------
# Geolocation / automation
# ---------------------------------------------------------------------------


class GeofenceClientData(BaseModel):
    is_at_home: bool | None = None
    name: str | None = None


# ---------------------------------------------------------------------------
# Concrete event models  (discriminated by `type`)
# ---------------------------------------------------------------------------


class ButtonEvent(BaseModel):
    type: Literal[ResourceType.BUTTON] = ResourceType.BUTTON
    id: UUID
    id_v1: str | None = None
    owner: OwnerReference
    button: ButtonData


class BellButtonEvent(BaseModel):
    type: Literal[ResourceType.BELL_BUTTON] = ResourceType.BELL_BUTTON
    id: UUID
    id_v1: str | None = None
    owner: OwnerReference
    button: ButtonData


class RelativeRotaryEvent(BaseModel):
    type: Literal[ResourceType.RELATIVE_ROTARY] = ResourceType.RELATIVE_ROTARY
    id: UUID
    id_v1: str | None = None
    owner: OwnerReference
    relative_rotary: RelativeRotaryData


class LightEvent(BaseModel):
    type: Literal[ResourceType.LIGHT] = ResourceType.LIGHT
    id: UUID
    id_v1: str | None = None
    owner: OwnerReference
    service_id: int | None = None
    on: OnState | None = None
    dimming: DimmingState | None = None
    color: ColorState | None = None
    color_temperature: ColorTemperature | None = None
    gradient: GradientState | None = None
    effects: EffectsState | None = None
    timed_effects: TimedEffectsState | None = None
    dynamics: DynamicsState | None = None
    alert: AlertState | None = None
    signaling: SignalingState | None = None
    mode: str | None = None


class GroupedLightEvent(BaseModel):
    type: Literal[ResourceType.GROUPED_LIGHT] = ResourceType.GROUPED_LIGHT
    id: UUID
    id_v1: str | None = None
    owner: OwnerReference | None = None
    on: OnState | None = None
    dimming: DimmingState | None = None
    color: ColorState | None = None
    color_temperature: ColorTemperature | None = None
    alert: AlertState | None = None
    signaling: SignalingState | None = None


class MotionEvent(BaseModel):
    type: Literal[ResourceType.MOTION] = ResourceType.MOTION
    id: UUID
    id_v1: str | None = None
    owner: OwnerReference
    motion: MotionData


class CameraMotionEvent(BaseModel):
    type: Literal[ResourceType.CAMERA_MOTION] = ResourceType.CAMERA_MOTION
    id: UUID
    id_v1: str | None = None
    owner: OwnerReference
    motion: MotionData


class TemperatureEvent(BaseModel):
    type: Literal[ResourceType.TEMPERATURE] = ResourceType.TEMPERATURE
    id: UUID
    id_v1: str | None = None
    owner: OwnerReference
    temperature: TemperatureData


class LightLevelEvent(BaseModel):
    type: Literal[ResourceType.LIGHT_LEVEL] = ResourceType.LIGHT_LEVEL
    id: UUID
    id_v1: str | None = None
    owner: OwnerReference
    light: LightLevelData


class ContactEvent(BaseModel):
    type: Literal[ResourceType.CONTACT] = ResourceType.CONTACT
    id: UUID
    id_v1: str | None = None
    owner: OwnerReference
    contact_report: ContactReport | None = None


class TamperEvent(BaseModel):
    type: Literal[ResourceType.TAMPER] = ResourceType.TAMPER
    id: UUID
    id_v1: str | None = None
    owner: OwnerReference
    tamper_reports: list[TamperReport] | None = None


class SceneEvent(BaseModel):
    type: Literal[ResourceType.SCENE] = ResourceType.SCENE
    id: UUID
    id_v1: str | None = None
    status: SceneStatus


class SmartSceneEvent(BaseModel):
    type: Literal[ResourceType.SMART_SCENE] = ResourceType.SMART_SCENE
    id: UUID
    id_v1: str | None = None
    state: SmartSceneState | None = None


class DevicePowerEvent(BaseModel):
    type: Literal[ResourceType.DEVICE_POWER] = ResourceType.DEVICE_POWER
    id: UUID
    id_v1: str | None = None
    owner: OwnerReference
    power_state: PowerStateData | None = None


class DeviceEvent(BaseModel):
    type: Literal[ResourceType.DEVICE] = ResourceType.DEVICE
    id: UUID
    id_v1: str | None = None
    metadata: DeviceMetadata | None = None
    product_data: ProductData | None = None
    services: list[ResourceReference] | None = None


class ZigbeeConnectivityEvent(BaseModel):
    type: Literal[ResourceType.ZIGBEE_CONNECTIVITY] = ResourceType.ZIGBEE_CONNECTIVITY
    id: UUID
    id_v1: str | None = None
    owner: OwnerReference
    status: ZigbeeStatus | None = None
    mac_address: str | None = None


class ZgpConnectivityEvent(BaseModel):
    type: Literal[ResourceType.ZGP_CONNECTIVITY] = ResourceType.ZGP_CONNECTIVITY
    id: UUID
    id_v1: str | None = None
    owner: OwnerReference
    status: ZigbeeStatus | None = None
    source_id: str | None = None


class WifiConnectivityEvent(BaseModel):
    type: Literal[ResourceType.WIFI_CONNECTIVITY] = ResourceType.WIFI_CONNECTIVITY
    id: UUID
    id_v1: str | None = None
    owner: OwnerReference
    status: WifiStatus | None = None


class GroupedMotionEvent(BaseModel):
    type: Literal[ResourceType.GROUPED_MOTION] = ResourceType.GROUPED_MOTION
    id: UUID
    id_v1: str | None = None
    owner: OwnerReference | None = None
    motion: GroupedMotionData | None = None


class GroupedLightLevelEvent(BaseModel):
    type: Literal[ResourceType.GROUPED_LIGHT_LEVEL] = ResourceType.GROUPED_LIGHT_LEVEL
    id: UUID
    id_v1: str | None = None
    owner: OwnerReference | None = None
    light: GroupedLightLevelData | None = None


class EntertainmentConfigurationEvent(BaseModel):
    type: Literal[ResourceType.ENTERTAINMENT_CONFIGURATION] = (
        ResourceType.ENTERTAINMENT_CONFIGURATION
    )
    id: UUID
    id_v1: str | None = None
    status: str | None = None  # "active" | "inactive"


class HomekitEvent(BaseModel):
    type: Literal[ResourceType.HOMEKIT] = ResourceType.HOMEKIT
    id: UUID
    id_v1: str | None = None
    status: str | None = None


class MatterEvent(BaseModel):
    type: Literal[ResourceType.MATTER] = ResourceType.MATTER
    id: UUID
    id_v1: str | None = None
    has_qr_code: bool | None = None


class GeofenceClientEvent(BaseModel):
    type: Literal[ResourceType.GEOFENCE_CLIENT] = ResourceType.GEOFENCE_CLIENT
    id: UUID
    id_v1: str | None = None
    name: str | None = None
    is_at_home: bool | None = None


HueEvent = Annotated[
    ButtonEvent
    | BellButtonEvent
    | RelativeRotaryEvent
    | LightEvent
    | GroupedLightEvent
    | MotionEvent
    | CameraMotionEvent
    | TemperatureEvent
    | LightLevelEvent
    | ContactEvent
    | TamperEvent
    | SceneEvent
    | SmartSceneEvent
    | DevicePowerEvent
    | DeviceEvent
    | ZigbeeConnectivityEvent
    | ZgpConnectivityEvent
    | WifiConnectivityEvent
    | GroupedMotionEvent
    | GroupedLightLevelEvent
    | EntertainmentConfigurationEvent
    | HomekitEvent
    | MatterEvent
    | GeofenceClientEvent,
    Field(discriminator="type"),
]


class UnknownEvent(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: UUID
    type: str
    id_v1: str | None = None
    owner: OwnerReference | None = None
    service_id: int | None = None

    @property
    def extra_fields(self) -> dict[str, Any]:
        return {
            k: v
            for k, v in self.__dict__.items()
            if k not in self.__class__.model_fields
        }
