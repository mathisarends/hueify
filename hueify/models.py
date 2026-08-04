from enum import StrEnum
from typing import Literal
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


class OnState(HueModel):
    on: bool


class DimmingState(HueModel):
    brightness: float = Field(ge=0, le=100)


class ColorTemperatureSchema(HueModel):
    mirek_minimum: int = Field(ge=50, le=1000)
    mirek_maximum: int = Field(ge=50, le=1000)


class ColorTemperatureState(HueModel):
    mirek: int | None = Field(default=None, ge=50, le=1000)
    mirek_valid: bool | None = None
    mirek_schema: ColorTemperatureSchema | None = None


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


class EffectsState(HueModel):
    effect: str | None = None
    status: str | None = None
    status_values: list[str] | None = None
    effect_values: list[str] | None = None


class TimedEffectsState(HueModel):
    effect: str | None = None
    duration: int | None = None
    status: str | None = None
    status_values: list[str] | None = None
    effect_values: list[str] | None = None


class DynamicsState(HueModel):
    status: str | None = None
    status_values: list[str] | None = None
    speed: float | None = Field(default=None, ge=0, le=1)
    speed_valid: bool | None = None


class AlertState(HueModel):
    action: str | None = None
    action_values: list[str] | None = None


class SignalingState(HueModel):
    signal: str | None = None
    duration: int | None = None
    colors: list[ColorXY] | None = None
    status: str | None = None
    signal_values: list[str] | None = None


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


class LightMetadata(HueModel):
    name: str
    archetype: LightArchetype | str | None = None


class Light(HueModel):
    id: UUID
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
    timed_effects: TimedEffectsState | None = None
    dynamics: DynamicsState | None = None
    alert: AlertState | None = None
    signaling: SignalingState | None = None
    mode: str | None = None


class LightUpdate(HueModel):
    on: OnState | None = None
    dimming: DimmingState | None = None
    color_temperature: ColorTemperatureState | None = None
    color: ColorState | None = None
    gradient: GradientState | None = None
    effects: EffectsState | None = None
    timed_effects: TimedEffectsState | None = None
    dynamics: DynamicsState | None = None
    alert: AlertState | None = None
    signaling: SignalingState | None = None


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


class GroupMetadata(HueModel):
    name: str
    archetype: GroupArchetype | str


class Group(HueModel):
    id: UUID
    metadata: GroupMetadata
    children: list[ResourceReference] = Field(default_factory=list)
    services: list[ResourceReference] = Field(default_factory=list)


class Room(Group):
    type: Literal[ResourceType.ROOM] = ResourceType.ROOM


class Zone(Group):
    type: Literal[ResourceType.ZONE] = ResourceType.ZONE


class GroupUpdate(HueModel):
    metadata: GroupMetadata | None = None
    children: list[ResourceReference] | None = None


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


class SceneMetadata(HueModel):
    name: str = Field(min_length=1, max_length=32)
    image: ImageResourceReference | None = None
    appdata: str | None = Field(default=None, min_length=1, max_length=16)


class ColorPaletteEntry(HueModel):
    color: ColorState


class DimmingPaletteEntry(HueModel):
    dimming: DimmingState


class ColorTemperaturePaletteEntry(HueModel):
    color_temperature: ColorTemperatureState


class EffectsPaletteEntry(HueModel):
    effects: EffectsState


class ScenePalette(HueModel):
    color: list[ColorPaletteEntry] = Field(default_factory=list)
    dimming: list[DimmingPaletteEntry] = Field(default_factory=list)
    color_temperature: list[ColorTemperaturePaletteEntry] = Field(default_factory=list)
    effects: list[EffectsPaletteEntry] = Field(default_factory=list)
    effects_v2: list[EffectsPaletteEntry] = Field(default_factory=list)


class Scene(HueModel):
    id: UUID
    type: Literal[ResourceType.SCENE] = ResourceType.SCENE
    metadata: SceneMetadata
    group: ResourceReference
    actions: list[SceneActionTarget] = Field(default_factory=list)
    palette: ScenePalette = Field(default_factory=ScenePalette)
    speed: float = Field(default=0.5, ge=0, le=1)
    auto_dynamic: bool = False
    status: SceneStatus | None = None
    id_v1: str | None = None


class SceneUpdate(HueModel):
    metadata: SceneMetadata | None = None
    actions: list[SceneActionTarget] | None = None
    palette: ScenePalette | None = None
    speed: float | None = Field(default=None, ge=0, le=1)
    auto_dynamic: bool | None = None


class SceneRecall(HueModel):
    action: SceneAction = SceneAction.ACTIVE
    duration: int | None = None
    dimming: DimmingState | None = None


class SceneRecallRequest(HueModel):
    recall: SceneRecall = Field(default_factory=SceneRecall)


class HueEvent(HueModel):
    id: UUID
    type: ResourceType


class LightEvent(LightUpdate, HueEvent):
    type: Literal[ResourceType.LIGHT] = ResourceType.LIGHT
    id_v1: str | None = None
    owner: ResourceReference | None = None


class RoomEvent(GroupUpdate, HueEvent):
    type: Literal[ResourceType.ROOM] = ResourceType.ROOM
    services: list[ResourceReference] | None = None


class ZoneEvent(GroupUpdate, HueEvent):
    type: Literal[ResourceType.ZONE] = ResourceType.ZONE
    services: list[ResourceReference] | None = None


class SceneEvent(SceneUpdate, HueEvent):
    type: Literal[ResourceType.SCENE] = ResourceType.SCENE
    status: SceneStatus | None = None
