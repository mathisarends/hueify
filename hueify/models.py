from datetime import datetime
from enum import StrEnum
from typing import Annotated, Any, Literal, Self
from uuid import UUID

from pydantic import Discriminator, Field, Tag, model_validator

from hueify._model_base import (
    HueApiError,
    HueApiResponse,
    HueModel,
    HueResource,
    NamedMetadata,
    NamedResource,
    ResourceIdentifier,
    ResourceReference,
    ResourceType,
)
from hueify._resource_models import (
    BehaviorInstance,
    BehaviorInstanceUpdate,
    BehaviorScript,
    BellButton,
    BellState,
    Bridge,
    BridgeHome,
    Button,
    ButtonConfiguration,
    ButtonReport,
    ButtonState,
    ButtonUpdate,
    CameraMotion,
    Contact,
    ContactReport,
    ControlMetadata,
    ConvenienceAreaMotion,
    Device,
    DevicePower,
    DeviceSoftwareUpdate,
    DeviceSoftwareUpdateUpdate,
    DeviceUpdate,
    DiscoveryAction,
    EnabledUpdate,
    Entertainment,
    EntertainmentSegment,
    EntertainmentSegments,
    GeofenceClient,
    GeofenceClientUpdate,
    Geolocation,
    GroupedLightLevel,
    GroupedMotion,
    Homekit,
    HomekitUpdate,
    IdentifyAction,
    LightLevel,
    LightLevelReport,
    LightLevelState,
    Matter,
    MatterAction,
    MatterFabric,
    MatterFabricData,
    MatterUpdate,
    MetadataUpdate,
    Motion,
    MotionAreaCandidate,
    MotionAreaConfiguration,
    MotionReport,
    MotionSensitivity,
    MotionSensitivityUpdate,
    MotionState,
    MotionUpdate,
    OwnedResource,
    PowerState,
    ProductData,
    RelativeRotary,
    RelativeRotaryState,
    RotaryReport,
    Rotation,
    SecurityAreaMotion,
    ServiceGroup,
    ServiceGroupUpdate,
    SmartScene,
    SmartSceneActiveTimeslot,
    SmartSceneCreate,
    SmartSceneDay,
    SmartSceneRecall,
    SmartSceneStartTime,
    SmartSceneTime,
    SmartSceneTimeslot,
    SmartSceneUpdate,
    SoftwareInstall,
    Speaker,
    SwitchInputConfiguration,
    SwitchInputConfigurationUpdate,
    Tamper,
    TamperReport,
    Temperature,
    TemperatureReport,
    TemperatureState,
    TimeZone,
    UserTest,
    UserTestUpdate,
    Weekday,
    WifiConnectivity,
    WifiSignalStrength,
    ZgpConnectivity,
    ZigbeeChannel,
    ZigbeeChannelValue,
    ZigbeeConnectivity,
    ZigbeeConnectivityUpdate,
    ZigbeeDeviceDiscovery,
    ZigbeeDeviceDiscoveryUpdate,
)


class OnState(HueModel):
    on: bool


class DimmingState(HueModel):
    brightness: float = Field(ge=0, le=100)
    min_dim_level: float | None = Field(default=None, ge=0, le=100)


class DimmingEventState(DimmingState):
    brightness: float | None = Field(default=None, ge=0, le=100)


class DimmingDeltaAction(StrEnum):
    UP = "up"
    DOWN = "down"
    STOP = "stop"


class DimmingDelta(HueModel):
    action: DimmingDeltaAction
    brightness_delta: float | None = Field(default=None, ge=0, le=100)


class ColorTemperatureSchema(HueModel):
    mirek_minimum: int = Field(ge=50, le=1000)
    mirek_maximum: int = Field(ge=50, le=1000)


class ColorTemperatureState(HueModel):
    mirek: int | None = Field(default=None, ge=50, le=1000)
    mirek_valid: bool | None = None
    mirek_schema: ColorTemperatureSchema | None = None


class ColorTemperatureDelta(HueModel):
    action: DimmingDeltaAction
    mirek_delta: int | None = Field(default=None, ge=0, le=347)


class ColorXY(HueModel):
    x: float = Field(ge=0, le=1)
    y: float = Field(ge=0, le=1)


class ColorGamut(HueModel):
    red: ColorXY | None = None
    green: ColorXY | None = None
    blue: ColorXY | None = None


class GamutType(StrEnum):
    A = "A"
    B = "B"
    C = "C"
    OTHER = "other"


class ColorState(HueModel):
    xy: ColorXY | None = None
    gamut: ColorGamut | None = None
    gamut_type: GamutType | None = None


class GradientPoint(HueModel):
    color: ColorState


class GradientState(HueModel):
    points: list[GradientPoint] = Field(default_factory=list)
    mode: str | None = None
    points_capable: int | None = None
    mode_values: list[str] | None = None
    pixel_count: int | None = None


class GradientUpdate(HueModel):
    points: list[GradientPoint] | None = Field(default=None, min_length=2, max_length=5)
    mode: str | None = None


class EffectsState(HueModel):
    effect: str | None = None
    status: str | None = None
    status_values: list[str] | None = None
    effect_values: list[str] | None = None


class EffectParameters(HueModel):
    color: ColorState | None = None
    color_temperature: ColorTemperatureState | None = None
    speed: float | None = Field(default=None, ge=0, le=1)


class EffectAction(HueModel):
    effect: str
    parameters: EffectParameters | None = None


class EffectStatus(HueModel):
    effect: str | None = None
    effect_values: list[str] | None = None
    parameters: EffectParameters | None = None


class EffectsV2State(HueModel):
    action: EffectAction | None = None
    status: EffectStatus | None = None


class EffectsV2Update(HueModel):
    action: EffectAction


class PowerupState(HueModel):
    preset: Literal["safety", "powerfail", "last_on_state", "custom"]
    configured: bool | None = None
    on: HueModel | None = None
    dimming: HueModel | None = None
    color: HueModel | None = None


class TimedEffectsState(HueModel):
    effect: str | None = None
    duration: int | None = Field(default=None, ge=0, le=21600000)
    status: str | None = None
    status_values: list[str] | None = None
    effect_values: list[str] | None = None


class DynamicsState(HueModel):
    status: str | None = None
    status_values: list[str] | None = None
    speed: float | None = Field(default=None, ge=0, le=1)
    speed_valid: bool | None = None
    duration: int | None = Field(default=None, ge=0)


class AlertState(HueModel):
    action: str | None = None
    action_values: list[str] | None = None


class SignalingState(HueModel):
    signal: str | None = None
    duration: int | None = Field(default=None, ge=0, le=65534000)
    color: list[ColorState] | None = Field(default=None, min_length=1, max_length=2)
    colors: list[ColorState | ColorXY] | None = None
    status: str | None = None
    signal_values: list[str] | None = None
    estimated_end: int | None = None


class SignalingUpdate(HueModel):
    signal: Literal["no_signal", "on_off", "on_off_color", "alternating"]
    duration: int | None = Field(default=None, ge=0, le=65534000)
    color: list[ColorState] | None = Field(default=None, min_length=1, max_length=2)


class LightArchetype(StrEnum):
    UNKNOWN_ARCHETYPE = "unknown_archetype"
    CLASSIC_BULB = "classic_bulb"
    SULTAN_BULB = "sultan_bulb"
    FLOOD_BULB = "flood_bulb"
    SPOT_BULB = "spot_bulb"
    CANDLE_BULB = "candle_bulb"
    LUSTER_BULB = "luster_bulb"
    PENDANT_ROUND = "pendant_round"
    PENDANT_LONG = "pendant_long"
    CEILING_ROUND = "ceiling_round"
    CEILING_SQUARE = "ceiling_square"
    FLOOR_SHADE = "floor_shade"
    FLOOR_LANTERN = "floor_lantern"
    TABLE_SHADE = "table_shade"
    RECESSED_CEILING = "recessed_ceiling"
    RECESSED_FLOOR = "recessed_floor"
    SINGLE_SPOT = "single_spot"
    DOUBLE_SPOT = "double_spot"
    TABLE_WASH = "table_wash"
    WALL_LANTERN = "wall_lantern"
    WALL_SHADE = "wall_shade"
    FLEXIBLE_LAMP = "flexible_lamp"
    GROUND_SPOT = "ground_spot"
    WALL_SPOT = "wall_spot"
    PLUG = "plug"
    HUE_GO = "hue_go"
    HUE_LIGHTSTRIP = "hue_lightstrip"
    HUE_IRIS = "hue_iris"
    HUE_BLOOM = "hue_bloom"
    BOLLARD = "bollard"
    WALL_WASHER = "wall_washer"
    HUE_PLAY = "hue_play"
    VINTAGE_BULB = "vintage_bulb"
    VINTAGE_CANDLE_BULB = "vintage_candle_bulb"
    ELLIPSE_BULB = "ellipse_bulb"
    TRIANGLE_BULB = "triangle_bulb"
    SMALL_GLOBE_BULB = "small_globe_bulb"
    LARGE_GLOBE_BULB = "large_globe_bulb"
    EDISON_BULB = "edison_bulb"
    CHRISTMAS_TREE = "christmas_tree"
    STRING_LIGHT = "string_light"
    HUE_CENTRIS = "hue_centris"
    HUE_LIGHTSTRIP_TV = "hue_lightstrip_tv"
    HUE_LIGHTSTRIP_PC = "hue_lightstrip_pc"
    HUE_TUBE = "hue_tube"
    HUE_SIGNE = "hue_signe"
    PENDANT_SPOT = "pendant_spot"
    CEILING_HORIZONTAL = "ceiling_horizontal"
    CEILING_TUBE = "ceiling_tube"
    UP_AND_DOWN = "up_and_down"
    UP_AND_DOWN_UP = "up_and_down_up"
    UP_AND_DOWN_DOWN = "up_and_down_down"
    HUE_FLOODLIGHT_CAMERA = "hue_floodlight_camera"
    TWILIGHT = "twilight"
    TWILIGHT_FRONT = "twilight_front"
    TWILIGHT_BACK = "twilight_back"
    HUE_PLAY_WALLWASHER = "hue_play_wallwasher"
    HUE_OMNIGLOW = "hue_omniglow"
    HUE_NEON = "hue_neon"
    STRING_GLOBE = "string_globe"
    STRING_PERMANENT = "string_permanent"


class LightMetadata(NamedMetadata):
    archetype: LightArchetype | str | None = None
    function: str | None = None
    fixed_mired: int | None = None


class LightMetadataUpdate(HueModel):
    name: str | None = None
    archetype: LightArchetype | str | None = None
    function: str | None = None


class LightStateMixin:
    """Flattened accessors for resources whose state lives in optional sub-models.

    Mixed into pydantic models alongside BaseModel; declares no fields of its
    own, so it never conflicts with the fields it reads off ``self``.
    """

    on: OnState | None
    dimming: DimmingState | None
    color_temperature: ColorTemperatureState | None
    color: ColorState | None

    @property
    def is_on(self) -> bool | None:
        return self.on.on if self.on else None

    @property
    def brightness(self) -> float | None:
        return self.dimming.brightness if self.dimming else None

    @property
    def mirek(self) -> int | None:
        return self.color_temperature.mirek if self.color_temperature else None

    @property
    def xy(self) -> ColorXY | None:
        return self.color.xy if self.color else None


class Light(NamedResource, LightStateMixin):
    type: Literal[ResourceType.LIGHT] = ResourceType.LIGHT
    id_v1: str | None = None
    owner: ResourceReference
    metadata: LightMetadata
    on: OnState
    dimming: DimmingState | None = None
    color_temperature: ColorTemperatureState | None = None
    color: ColorState | None = None
    gradient: GradientState | None = None
    effects: EffectsState | None = None
    effects_v2: EffectsV2State | None = None
    timed_effects: TimedEffectsState | None = None
    dynamics: DynamicsState | None = None
    alert: AlertState | None = None
    signaling: SignalingState | None = None
    powerup: PowerupState | None = None
    identify: HueModel | None = None
    service_id: int | None = None
    mode: str | None = None


class LightUpdate(HueModel, LightStateMixin):
    metadata: LightMetadataUpdate | None = None
    identify: IdentifyAction | None = None
    on: OnState | None = None
    dimming: DimmingState | None = None
    dimming_delta: DimmingDelta | None = None
    color_temperature: ColorTemperatureState | None = None
    color_temperature_delta: ColorTemperatureDelta | None = None
    color: ColorState | None = None
    gradient: GradientUpdate | None = None
    effects: EffectsState | None = None
    effects_v2: EffectsV2Update | None = None
    timed_effects: TimedEffectsState | None = None
    dynamics: DynamicsState | None = None
    alert: AlertState | None = None
    signaling: SignalingUpdate | None = None
    powerup: PowerupState | None = None
    mode: str | None = None


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


class GroupMetadata(NamedMetadata):
    archetype: GroupArchetype | str


class GroupMetadataUpdate(HueModel):
    name: str | None = Field(default=None, min_length=1, max_length=32)
    archetype: GroupArchetype | str | None = None


class Group(NamedResource):
    metadata: GroupMetadata
    children: list[ResourceReference] = Field(default_factory=list)
    services: list[ResourceReference] = Field(default_factory=list)


class Room(Group):
    type: Literal[ResourceType.ROOM] = ResourceType.ROOM


class Zone(Group):
    type: Literal[ResourceType.ZONE] = ResourceType.ZONE


class GroupUpdate(HueModel):
    metadata: GroupMetadataUpdate | GroupMetadata | None = None
    children: list[ResourceReference] | None = None


class GroupCreate(GroupUpdate):
    metadata: GroupMetadata
    children: list[ResourceReference] = Field(default_factory=list)


class GroupedLight(HueModel, LightStateMixin):
    """Aggregated light service a room or zone is controlled through."""

    id: UUID
    type: Literal[ResourceType.GROUPED_LIGHT] = ResourceType.GROUPED_LIGHT
    id_v1: str | None = None
    owner: ResourceReference | None = None
    on: OnState | None = None
    dimming: DimmingState | None = None
    color_temperature: ColorTemperatureState | None = None
    color: ColorState | None = None
    dynamics: DynamicsState | None = None
    alert: AlertState | None = None
    signaling: SignalingState | None = None


class SceneStatusValue(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    STATIC = "static"
    DYNAMIC_PALETTE = "dynamic_palette"


class SceneStatus(HueModel):
    active: SceneStatusValue | None = None
    last_recall: str | None = None


class SceneAction(StrEnum):
    ACTIVE = "active"
    DYNAMIC_PALETTE = "dynamic_palette"
    STATIC = "static"


class SceneActionTarget(HueModel):
    target: ResourceReference
    action: LightUpdate


class ImageResourceReference(HueModel):
    rid: UUID
    rtype: Literal[ResourceType.PUBLIC_IMAGE] = ResourceType.PUBLIC_IMAGE


class SceneMetadata(NamedMetadata):
    name: str = Field(min_length=1, max_length=32)
    image: ImageResourceReference | None = None
    appdata: str | None = Field(default=None, min_length=1, max_length=16)


class SceneMetadataUpdate(HueModel):
    name: str | None = Field(default=None, min_length=1, max_length=32)
    image: ImageResourceReference | None = None
    appdata: str | None = Field(default=None, min_length=1, max_length=16)


class ColorPaletteEntry(HueModel):
    color: ColorState
    dimming: DimmingState | None = None


class DimmingPaletteEntry(HueModel):
    dimming: DimmingState


class ColorTemperaturePaletteEntry(HueModel):
    color_temperature: ColorTemperatureState
    dimming: DimmingState | None = None


class EffectsPaletteEntry(HueModel):
    effect: str | None = None
    effects: EffectsState | None = None


class EffectsV2PaletteEntry(HueModel):
    effect: str
    parameters: EffectParameters | None = None


class ScenePalette(HueModel):
    color: list[ColorPaletteEntry] = Field(default_factory=list)
    dimming: list[DimmingState] = Field(default_factory=list, max_length=1)
    color_temperature: list[ColorTemperaturePaletteEntry] = Field(default_factory=list)
    effects: list[EffectAction] = Field(default_factory=list, max_length=3)
    effects_v2: list[EffectsV2PaletteEntry] = Field(default_factory=list)


class Scene(NamedResource):
    type: Literal[ResourceType.SCENE] = ResourceType.SCENE
    metadata: SceneMetadata
    group: ResourceReference
    actions: list[SceneActionTarget] = Field(default_factory=list)
    palette: ScenePalette = Field(default_factory=ScenePalette)
    speed: float = Field(default=0.5, ge=0, le=1)
    auto_dynamic: bool = False
    status: SceneStatus | None = None
    id_v1: str | None = None


class SceneRecall(HueModel):
    action: SceneAction = SceneAction.ACTIVE
    duration: int | None = Field(default=None, ge=0)
    dimming: DimmingState | None = None


class SceneUpdate(HueModel):
    metadata: SceneMetadataUpdate | SceneMetadata | None = None
    actions: list[SceneActionTarget] | None = None
    palette: ScenePalette | None = None
    speed: float | None = Field(default=None, ge=0, le=1)
    auto_dynamic: bool | None = None
    recall: SceneRecall | None = None


class SceneCreate(HueModel):
    metadata: SceneMetadata
    group: ResourceReference
    actions: list[SceneActionTarget]
    palette: ScenePalette | None = None
    speed: float | None = Field(default=None, ge=0, le=1)
    auto_dynamic: bool | None = None

    @model_validator(mode="after")
    def validate_group(self) -> Self:
        if self.group.rtype not in {ResourceType.ROOM, ResourceType.ZONE}:
            raise ValueError("A scene belongs to a room or zone")
        if any(action.target.rtype != ResourceType.LIGHT for action in self.actions):
            raise ValueError("Scene actions target lights")
        return self


class SceneRecallRequest(HueModel):
    recall: SceneRecall = Field(default_factory=SceneRecall)


class EntertainmentConfigurationType(StrEnum):
    SCREEN = "screen"
    MONITOR = "monitor"
    MUSIC = "music"
    THREE_D_SPACE = "3dspace"
    OTHER = "other"


class StreamingStatus(StrEnum):
    INACTIVE = "inactive"
    ACTIVE = "active"


class EntertainmentPosition(HueModel):
    """Where a channel sits in the room, as a -1 to 1 cube around the viewer."""

    x: float = Field(ge=-1, le=1)
    y: float = Field(ge=-1, le=1)
    z: float = Field(ge=-1, le=1)


class EntertainmentChannelMember(HueModel):
    service: ResourceReference
    index: int


class EntertainmentChannel(HueModel):
    """One addressable slot of a streaming frame, and the segments it drives."""

    channel_id: int = Field(ge=0, le=255)
    position: EntertainmentPosition
    members: list[EntertainmentChannelMember] = Field(default_factory=list)


class EntertainmentServiceLocation(HueModel):
    service: ResourceReference
    position: EntertainmentPosition | None = None
    positions: list[EntertainmentPosition] = Field(default_factory=list)
    equalization_factor: float | None = None


class EntertainmentLocations(HueModel):
    service_locations: list[EntertainmentServiceLocation] = Field(default_factory=list)


class StreamProxyMode(StrEnum):
    AUTO = "auto"
    MANUAL = "manual"


class StreamProxy(HueModel):
    """The light the bridge routes the stream through."""

    mode: StreamProxyMode | str | None = None
    node: ResourceReference | None = None


class EntertainmentConfiguration(NamedResource):
    """An entertainment area: the channels a streaming session can address."""

    type: Literal[ResourceType.ENTERTAINMENT_CONFIGURATION] = (
        ResourceType.ENTERTAINMENT_CONFIGURATION
    )
    id_v1: str | None = None
    configuration_type: EntertainmentConfigurationType | str | None = None
    status: StreamingStatus | str | None = None
    active_streamer: ResourceReference | None = None
    stream_proxy: StreamProxy | None = None
    channels: list[EntertainmentChannel] = Field(default_factory=list)
    locations: EntertainmentLocations | None = None
    light_services: list[ResourceReference] = Field(default_factory=list)

    @property
    def is_streaming(self) -> bool:
        return self.status == StreamingStatus.ACTIVE


class StreamAction(StrEnum):
    START = "start"
    STOP = "stop"


class EntertainmentConfigurationUpdate(HueModel):
    action: StreamAction | None = None
    metadata: NamedMetadata | None = None
    configuration_type: EntertainmentConfigurationType | None = None
    stream_proxy: StreamProxy | None = None


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


__all__ = [
    "AlertState",
    "AnyHueEvent",
    "BehaviorInstance",
    "BehaviorInstanceEvent",
    "BehaviorInstanceUpdate",
    "BehaviorScript",
    "BehaviorScriptEvent",
    "BellButton",
    "BellButtonEvent",
    "BellState",
    "Bridge",
    "BridgeEvent",
    "BridgeHome",
    "BridgeHomeEvent",
    "Button",
    "ButtonConfiguration",
    "ButtonEvent",
    "ButtonReport",
    "ButtonState",
    "ButtonUpdate",
    "CameraMotion",
    "CameraMotionEvent",
    "ColorGamut",
    "ColorPaletteEntry",
    "ColorState",
    "ColorTemperatureDelta",
    "ColorTemperaturePaletteEntry",
    "ColorTemperatureSchema",
    "ColorTemperatureState",
    "ColorXY",
    "Contact",
    "ContactEvent",
    "ContactReport",
    "ControlMetadata",
    "ConvenienceAreaMotion",
    "ConvenienceAreaMotionEvent",
    "Device",
    "DeviceEvent",
    "DevicePower",
    "DevicePowerEvent",
    "DeviceSoftwareUpdate",
    "DeviceSoftwareUpdateEvent",
    "DeviceSoftwareUpdateUpdate",
    "DeviceUpdate",
    "DimmingDelta",
    "DimmingDeltaAction",
    "DimmingEventState",
    "DimmingPaletteEntry",
    "DimmingState",
    "DiscoveryAction",
    "DynamicsState",
    "EffectAction",
    "EffectParameters",
    "EffectStatus",
    "EffectsPaletteEntry",
    "EffectsState",
    "EffectsV2PaletteEntry",
    "EffectsV2State",
    "EffectsV2Update",
    "EnabledUpdate",
    "Entertainment",
    "EntertainmentChannel",
    "EntertainmentChannelMember",
    "EntertainmentConfiguration",
    "EntertainmentConfigurationEvent",
    "EntertainmentConfigurationType",
    "EntertainmentConfigurationUpdate",
    "EntertainmentEvent",
    "EntertainmentLocations",
    "EntertainmentPosition",
    "EntertainmentSegment",
    "EntertainmentSegments",
    "EntertainmentServiceLocation",
    "GamutType",
    "GeofenceClient",
    "GeofenceClientEvent",
    "GeofenceClientUpdate",
    "Geolocation",
    "GeolocationEvent",
    "GradientPoint",
    "GradientState",
    "GradientUpdate",
    "Group",
    "GroupArchetype",
    "GroupCreate",
    "GroupMetadata",
    "GroupMetadataUpdate",
    "GroupUpdate",
    "GroupedLight",
    "GroupedLightEvent",
    "GroupedLightLevel",
    "GroupedLightLevelEvent",
    "GroupedMotion",
    "GroupedMotionEvent",
    "Homekit",
    "HomekitEvent",
    "HomekitUpdate",
    "HueApiError",
    "HueApiResponse",
    "HueEvent",
    "HueEventMessage",
    "HueModel",
    "HueResource",
    "IdentifyAction",
    "ImageResourceReference",
    "Light",
    "LightArchetype",
    "LightEvent",
    "LightLevel",
    "LightLevelEvent",
    "LightLevelReport",
    "LightLevelState",
    "LightMetadata",
    "LightMetadataUpdate",
    "LightStateMixin",
    "LightUpdate",
    "Matter",
    "MatterAction",
    "MatterEvent",
    "MatterFabric",
    "MatterFabricData",
    "MatterFabricEvent",
    "MatterUpdate",
    "MetadataUpdate",
    "Motion",
    "MotionAreaCandidate",
    "MotionAreaCandidateEvent",
    "MotionAreaConfiguration",
    "MotionAreaConfigurationEvent",
    "MotionEvent",
    "MotionReport",
    "MotionSensitivity",
    "MotionSensitivityUpdate",
    "MotionState",
    "MotionUpdate",
    "NamedMetadata",
    "NamedResource",
    "OnState",
    "OwnedResource",
    "PowerState",
    "PowerupState",
    "ProductData",
    "RelativeRotary",
    "RelativeRotaryEvent",
    "RelativeRotaryState",
    "ResourceIdentifier",
    "ResourceReference",
    "ResourceType",
    "Room",
    "RoomEvent",
    "RotaryReport",
    "Rotation",
    "Scene",
    "SceneAction",
    "SceneActionTarget",
    "SceneCreate",
    "SceneEvent",
    "SceneMetadata",
    "SceneMetadataUpdate",
    "ScenePalette",
    "SceneRecall",
    "SceneRecallRequest",
    "SceneStatus",
    "SceneStatusValue",
    "SceneUpdate",
    "SecurityAreaMotion",
    "SecurityAreaMotionEvent",
    "ServiceGroup",
    "ServiceGroupEvent",
    "ServiceGroupUpdate",
    "SignalingState",
    "SignalingUpdate",
    "SmartScene",
    "SmartSceneActiveTimeslot",
    "SmartSceneCreate",
    "SmartSceneDay",
    "SmartSceneEvent",
    "SmartSceneRecall",
    "SmartSceneStartTime",
    "SmartSceneTime",
    "SmartSceneTimeslot",
    "SmartSceneUpdate",
    "SoftwareInstall",
    "Speaker",
    "SpeakerEvent",
    "StreamAction",
    "StreamProxy",
    "StreamProxyMode",
    "StreamingStatus",
    "SwitchInputConfiguration",
    "SwitchInputConfigurationEvent",
    "SwitchInputConfigurationUpdate",
    "Tamper",
    "TamperEvent",
    "TamperReport",
    "Temperature",
    "TemperatureEvent",
    "TemperatureReport",
    "TemperatureState",
    "TimeZone",
    "TimedEffectsState",
    "UserTest",
    "UserTestUpdate",
    "Weekday",
    "WifiConnectivity",
    "WifiConnectivityEvent",
    "WifiSignalStrength",
    "ZgpConnectivity",
    "ZgpConnectivityEvent",
    "ZigbeeChannel",
    "ZigbeeChannelValue",
    "ZigbeeConnectivity",
    "ZigbeeConnectivityEvent",
    "ZigbeeConnectivityUpdate",
    "ZigbeeDeviceDiscovery",
    "ZigbeeDeviceDiscoveryEvent",
    "ZigbeeDeviceDiscoveryUpdate",
    "Zone",
    "ZoneEvent",
]
