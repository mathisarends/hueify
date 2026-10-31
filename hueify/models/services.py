"""CLIP v2 resources beyond lighting.

Field definitions are based on the public OpenHue specification; see
docs/clip-v2-coverage.md for the pinned reference and remaining verification.
Optional state fields also accommodate services with differing capabilities.
"""

from datetime import datetime
from typing import Any, Literal, Self
from uuid import UUID

from pydantic import Field, model_validator

from hueify.models.base import (
    HueModel,
    HueResource,
    IdentifyAction,
    MetadataUpdate,
    ResourceReference,
    ResourceType,
)


class UserTest(HueModel):
    usertest: bool | None = None
    status: str | None = None


class UserTestUpdate(HueModel):
    usertest: bool


class ProductData(HueModel):
    model_id: str | None = None
    manufacturer_name: str | None = None
    product_name: str | None = None
    product_archetype: str | None = None
    certified: bool | None = None
    software_version: str | None = None
    hardware_platform_type: str | None = None


class OwnedResource(HueResource):
    owner: ResourceReference | None = None


class NamedServiceMixin:
    metadata: MetadataUpdate | None

    @property
    def name(self) -> str | None:
        return self.metadata.name if self.metadata else None


class Device(OwnedResource, NamedServiceMixin):
    type: Literal[ResourceType.DEVICE] = ResourceType.DEVICE
    metadata: MetadataUpdate | None = None
    product_data: ProductData | None = None
    services: list[ResourceReference] = Field(default_factory=list)
    identify: HueModel | None = None
    usertest: UserTest | None = None


class DeviceUpdate(HueModel):
    metadata: MetadataUpdate | None = None
    identify: IdentifyAction | None = None
    usertest: UserTestUpdate | None = None


class PowerState(HueModel):
    battery_state: str | None = None
    battery_level: int | None = Field(default=None, ge=0, le=100)


class DevicePower(OwnedResource):
    type: Literal[ResourceType.DEVICE_POWER] = ResourceType.DEVICE_POWER
    power_state: PowerState | None = None


class SoftwareInstall(HueModel):
    install_state: Literal["install"] = "install"


class DeviceSoftwareUpdate(OwnedResource):
    type: Literal[ResourceType.DEVICE_SOFTWARE_UPDATE] = (
        ResourceType.DEVICE_SOFTWARE_UPDATE
    )
    state: str | None = None
    problems: list[str] = Field(default_factory=list)


class DeviceSoftwareUpdateUpdate(HueModel):
    install: SoftwareInstall | None = None


class TimeZone(HueModel):
    time_zone: str


class Bridge(OwnedResource):
    type: Literal[ResourceType.BRIDGE] = ResourceType.BRIDGE
    bridge_id: str | None = None
    time_zone: TimeZone | None = None


class BridgeHome(HueResource):
    type: Literal[ResourceType.BRIDGE_HOME] = ResourceType.BRIDGE_HOME
    children: list[ResourceReference] = Field(default_factory=list)
    services: list[ResourceReference] = Field(default_factory=list)


class ServiceGroup(HueResource):
    type: Literal[ResourceType.SERVICE_GROUP] = ResourceType.SERVICE_GROUP
    services: list[ResourceReference] = Field(default_factory=list)


class ServiceGroupUpdate(HueModel):
    services: list[ResourceReference] | None = None


class EnabledUpdate(HueModel):
    enabled: bool | None = None


class MotionReport(HueModel):
    changed: datetime | None = None
    motion: bool | None = None


class MotionState(HueModel):
    motion: bool | None = None
    motion_valid: bool | None = None
    motion_report: MotionReport | None = None

    @property
    def detected(self) -> bool | None:
        if self.motion_report is not None:
            return self.motion_report.motion
        return self.motion if self.motion_valid is not False else None


class MotionSensitivity(HueModel):
    sensitivity: int | None = Field(default=None, ge=0)
    sensitivity_max: int | None = Field(default=None, ge=0)
    status: str | None = None


class MotionSensitivityUpdate(HueModel):
    sensitivity: int = Field(ge=0)


class MotionStateMixin:
    motion: MotionState | None

    @property
    def detected(self) -> bool | None:
        return self.motion.detected if self.motion else None


class Motion(OwnedResource, MotionStateMixin):
    type: Literal[ResourceType.MOTION] = ResourceType.MOTION
    enabled: bool | None = None
    motion: MotionState | None = None
    sensitivity: MotionSensitivity | None = None


class MotionUpdate(EnabledUpdate):
    sensitivity: MotionSensitivityUpdate | None = None


class CameraMotion(OwnedResource):
    type: Literal[ResourceType.CAMERA_MOTION] = ResourceType.CAMERA_MOTION
    enabled: bool | None = None
    motion: MotionState | None = None


class GroupedMotion(OwnedResource):
    type: Literal[ResourceType.GROUPED_MOTION] = ResourceType.GROUPED_MOTION
    motion: MotionState | None = None


class TemperatureReport(HueModel):
    changed: datetime | None = None
    temperature: float | None = None


class TemperatureState(HueModel):
    temperature: float | None = None
    temperature_valid: bool | None = None
    temperature_report: TemperatureReport | None = None


class TemperatureStateMixin:
    temperature: TemperatureState | None

    @property
    def celsius(self) -> float | None:
        if self.temperature is None:
            return None
        if self.temperature.temperature_report is not None:
            return self.temperature.temperature_report.temperature
        if self.temperature.temperature_valid is False:
            return None
        return self.temperature.temperature


class Temperature(OwnedResource, TemperatureStateMixin):
    type: Literal[ResourceType.TEMPERATURE] = ResourceType.TEMPERATURE
    enabled: bool | None = None
    temperature: TemperatureState | None = None


class LightLevelReport(HueModel):
    changed: datetime | None = None
    light_level: int | None = None


class LightLevelState(HueModel):
    light_level: int | None = None
    light_level_valid: bool | None = None
    light_level_report: LightLevelReport | None = None

    @property
    def lux(self) -> float | None:
        if self.light_level_report is not None:
            value = self.light_level_report.light_level
        elif self.light_level_valid is not False:
            value = self.light_level
        else:
            value = None
        return 10 ** ((value - 1) / 10000) if value is not None else None


class LightLevelStateMixin:
    light: LightLevelState | None

    @property
    def lux(self) -> float | None:
        return self.light.lux if self.light else None


class LightLevel(OwnedResource, LightLevelStateMixin):
    type: Literal[ResourceType.LIGHT_LEVEL] = ResourceType.LIGHT_LEVEL
    enabled: bool | None = None
    light: LightLevelState | None = None


class GroupedLightLevel(OwnedResource):
    type: Literal[ResourceType.GROUPED_LIGHT_LEVEL] = ResourceType.GROUPED_LIGHT_LEVEL
    light: LightLevelState | None = None


class ControlMetadata(HueModel):
    control_id: int | None = None


class ButtonReport(HueModel):
    updated: datetime | None = None
    event: str | None = None


class ButtonState(HueModel):
    button_report: ButtonReport | None = None
    last_event: str | None = None
    repeat_interval: int | None = Field(default=None, ge=0)
    event_values: list[str] | None = None


class Button(OwnedResource):
    type: Literal[ResourceType.BUTTON] = ResourceType.BUTTON
    metadata: ControlMetadata | None = None
    button: ButtonState | None = None


class ButtonConfiguration(HueModel):
    repeat_interval: int | None = Field(default=None, ge=0)


class ButtonUpdate(HueModel):
    metadata: ControlMetadata | None = None
    button: ButtonConfiguration | None = None


class BellState(HueModel):
    bell_report: ButtonReport | None = None
    last_event: str | None = None


class BellButton(OwnedResource):
    type: Literal[ResourceType.BELL_BUTTON] = ResourceType.BELL_BUTTON
    metadata: ControlMetadata | None = None
    bell: BellState | None = None


class Rotation(HueModel):
    direction: str | None = None
    steps: int | None = None
    duration: int | None = None


class RotaryReport(HueModel):
    updated: datetime | None = None
    action: str | None = None
    rotation: Rotation | None = None


class RelativeRotaryState(HueModel):
    rotary_report: RotaryReport | None = None
    last_event: RotaryReport | None = None


class RelativeRotary(OwnedResource):
    type: Literal[ResourceType.RELATIVE_ROTARY] = ResourceType.RELATIVE_ROTARY
    metadata: ControlMetadata | None = None
    relative_rotary: RelativeRotaryState | None = None


class ContactReport(HueModel):
    changed: datetime | None = None
    state: str | None = None


class Contact(OwnedResource):
    type: Literal[ResourceType.CONTACT] = ResourceType.CONTACT
    enabled: bool | None = None
    contact_report: ContactReport | None = None


class TamperReport(HueModel):
    changed: datetime | None = None
    source: str | None = None
    state: str | None = None


class Tamper(OwnedResource):
    type: Literal[ResourceType.TAMPER] = ResourceType.TAMPER
    tamper_reports: list[TamperReport] = Field(default_factory=list)


type ZigbeeChannelValue = Literal[
    "channel_11", "channel_15", "channel_20", "channel_25"
]


class ZigbeeChannel(HueModel):
    value: ZigbeeChannelValue | None = None
    status: str | None = None


class ZigbeeConnectivity(OwnedResource):
    type: Literal[ResourceType.ZIGBEE_CONNECTIVITY] = ResourceType.ZIGBEE_CONNECTIVITY
    status: str | None = None
    mac_address: str | None = None
    channel: ZigbeeChannel | None = None
    extended_pan_id: str | None = None


class ZigbeeConnectivityUpdate(HueModel):
    channel: ZigbeeChannel | None = None


class ZgpConnectivity(OwnedResource):
    type: Literal[ResourceType.ZGP_CONNECTIVITY] = ResourceType.ZGP_CONNECTIVITY
    status: str | None = None
    source_id: str | None = None


class WifiSignalStrength(HueModel):
    status: str | None = None
    value: int | None = None


class WifiConnectivity(OwnedResource):
    type: Literal[ResourceType.WIFI_CONNECTIVITY] = ResourceType.WIFI_CONNECTIVITY
    status: str | None = None
    mac_address: str | None = None
    signal_strength: WifiSignalStrength | None = None


class DiscoveryAction(HueModel):
    action_type: Literal["search"] = "search"


class ZigbeeDeviceDiscovery(OwnedResource):
    type: Literal[ResourceType.ZIGBEE_DEVICE_DISCOVERY] = (
        ResourceType.ZIGBEE_DEVICE_DISCOVERY
    )
    status: str | None = None


class ZigbeeDeviceDiscoveryUpdate(HueModel):
    action: DiscoveryAction | None = None


class EntertainmentSegment(HueModel):
    start: int
    length: int


class EntertainmentSegments(HueModel):
    configurable: bool | None = None
    max_segments: int | None = None
    segments: list[EntertainmentSegment] = Field(default_factory=list)


class Entertainment(OwnedResource):
    type: Literal[ResourceType.ENTERTAINMENT] = ResourceType.ENTERTAINMENT
    renderer: bool | None = None
    proxy: bool | None = None
    max_streams: int | None = None
    segments: EntertainmentSegments | None = None


class Speaker(OwnedResource):
    type: Literal[ResourceType.SPEAKER] = ResourceType.SPEAKER
    alerts: list[str] = Field(default_factory=list)


class BehaviorScript(HueResource, NamedServiceMixin):
    type: Literal[ResourceType.BEHAVIOR_SCRIPT] = ResourceType.BEHAVIOR_SCRIPT
    description: str | None = None
    configuration_schema: dict[str, Any] | None = None
    trigger_schema: dict[str, Any] | None = None
    state_schema: dict[str, Any] | None = None
    version: str | None = None
    metadata: MetadataUpdate | None = None


class BehaviorInstance(HueResource, NamedServiceMixin):
    type: Literal[ResourceType.BEHAVIOR_INSTANCE] = ResourceType.BEHAVIOR_INSTANCE
    script_id: UUID | None = None
    enabled: bool | None = None
    state: dict[str, Any] | None = None
    configuration: dict[str, Any] | None = None
    dependees: list[ResourceReference] = Field(default_factory=list)
    status: str | None = None
    last_error: str | None = None
    metadata: MetadataUpdate | None = None


class BehaviorInstanceUpdate(EnabledUpdate):
    configuration: dict[str, Any] | None = None
    metadata: MetadataUpdate | None = None


class GeofenceClient(HueResource):
    type: Literal[ResourceType.GEOFENCE_CLIENT] = ResourceType.GEOFENCE_CLIENT
    name: str | None = None
    is_at_home: bool | None = None


class GeofenceClientUpdate(HueModel):
    name: str | None = None
    is_at_home: bool | None = None


class Geolocation(HueResource):
    type: Literal[ResourceType.GEOLOCATION] = ResourceType.GEOLOCATION
    is_configured: bool | None = None


class Homekit(OwnedResource):
    type: Literal[ResourceType.HOMEKIT] = ResourceType.HOMEKIT
    status: str | None = None
    action: str | None = None


class HomekitUpdate(HueModel):
    action: Literal["homekit_reset"] | None = None


class Matter(OwnedResource):
    type: Literal[ResourceType.MATTER] = ResourceType.MATTER
    has_qr_code: bool | None = None
    max_fabrics: int | None = None


class MatterAction(HueModel):
    action_type: Literal["matter_reset"] = "matter_reset"


class MatterUpdate(HueModel):
    action: MatterAction | None = None


class MatterFabricData(HueModel):
    label: str | None = None
    vendor_id: int | None = None


class MatterFabric(OwnedResource):
    type: Literal[ResourceType.MATTER_FABRIC] = ResourceType.MATTER_FABRIC
    status: str | None = None
    fabric_data: MatterFabricData | None = None
    creation_time: datetime | None = None


class ConvenienceAreaMotion(OwnedResource):
    type: Literal[ResourceType.CONVENIENCE_AREA_MOTION] = (
        ResourceType.CONVENIENCE_AREA_MOTION
    )
    enabled: bool | None = None
    motion: MotionState | None = None


class SecurityAreaMotion(OwnedResource):
    type: Literal[ResourceType.SECURITY_AREA_MOTION] = ResourceType.SECURITY_AREA_MOTION
    enabled: bool | None = None
    motion: MotionState | None = None


class MotionAreaCandidate(OwnedResource):
    type: Literal[ResourceType.MOTION_AREA_CANDIDATE] = (
        ResourceType.MOTION_AREA_CANDIDATE
    )
    motion_sensors: list[ResourceReference] = Field(default_factory=list)


class MotionAreaConfiguration(OwnedResource):
    type: Literal[ResourceType.MOTION_AREA_CONFIGURATION] = (
        ResourceType.MOTION_AREA_CONFIGURATION
    )
    enabled: bool | None = None
    motion_sensors: list[ResourceReference] = Field(default_factory=list)


class SwitchInputConfiguration(OwnedResource):
    """New wall-switch configuration; switch_mode values depend on the bridge."""

    type: Literal[ResourceType.SWITCH_INPUT_CONFIGURATION] = (
        ResourceType.SWITCH_INPUT_CONFIGURATION
    )
    switch_mode: str | HueModel | None = None


class SwitchInputConfigurationUpdate(HueModel):
    switch_mode: str | HueModel | None = None


type Weekday = Literal[
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"
]


class SmartSceneTime(HueModel):
    hour: int = Field(ge=0, le=23)
    minute: int = Field(ge=0, le=59)
    second: int = Field(default=0, ge=0, le=59)


class SmartSceneStartTime(HueModel):
    kind: Literal["time", "sunset"]
    time: SmartSceneTime | None = None

    @model_validator(mode="after")
    def validate_time(self) -> Self:
        if (self.kind == "time") != (self.time is not None):
            raise ValueError("Include time exactly when kind is 'time'")
        return self


class SmartSceneTimeslot(HueModel):
    start_time: SmartSceneStartTime
    target: ResourceReference


class SmartSceneDay(HueModel):
    timeslots: list[SmartSceneTimeslot]
    recurrence: list[Weekday]


class SmartSceneActiveTimeslot(HueModel):
    timeslot_id: int | None = None
    weekday: Weekday | None = None


class SmartScene(HueResource):
    type: Literal[ResourceType.SMART_SCENE] = ResourceType.SMART_SCENE
    metadata: MetadataUpdate
    group: ResourceReference
    week_timeslots: list[SmartSceneDay] = Field(default_factory=list)
    transition_duration: int | None = Field(default=None, ge=0)
    active_timeslot: SmartSceneActiveTimeslot | None = None
    state: str | None = None

    @property
    def name(self) -> str | None:
        return self.metadata.name if self.metadata else None


class SmartSceneRecall(HueModel):
    action: Literal["activate", "deactivate"]


class SmartSceneUpdate(HueModel):
    metadata: MetadataUpdate | None = None
    week_timeslots: list[SmartSceneDay] | None = None
    transition_duration: int | None = Field(default=None, ge=0)
    recall: SmartSceneRecall | None = None


class SmartSceneCreate(SmartSceneUpdate):
    metadata: MetadataUpdate
    group: ResourceReference
    week_timeslots: list[SmartSceneDay]

    @model_validator(mode="after")
    def validate_creation(self) -> Self:
        if self.metadata.name is None:
            raise ValueError("A smart scene needs a name")
        if self.group.rtype not in {ResourceType.ROOM, ResourceType.ZONE}:
            raise ValueError("A smart scene belongs to a room or zone")
        return self
