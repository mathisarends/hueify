"""Lighting, groups, scenes, and entertainment-area payloads."""

from enum import StrEnum
from typing import Literal, Self
from uuid import UUID

from pydantic import Field, model_validator

from hueify.models.base import (
    HueModel,
    HueRequest,
    HueResource,
    IdentifyAction,
    NamedMetadata,
    NamedResource,
    ResourceReference,
    ResourceType,
)


class OnState(HueModel):
    on: bool


class DimmingState(HueModel):
    brightness: float = Field(ge=0, le=100)
    min_dim_level: float | None = Field(default=None, ge=0, le=100)


class DimmingEventState(HueModel):
    brightness: float | None = Field(default=None, ge=0, le=100)
    min_dim_level: float | None = Field(default=None, ge=0, le=100)


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


class GradientUpdate(HueRequest):
    points: list[GradientPoint] | None = Field(default=None, min_length=2, max_length=5)
    mode: str | None = None


class GradientEventState(HueModel):
    points: list[GradientPoint] | None = None
    mode: str | None = None
    points_capable: int | None = None
    mode_values: list[str] | None = None
    pixel_count: int | None = None


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


class EffectsV2Update(HueRequest):
    action: EffectAction


class PowerupState(HueModel):
    preset: Literal["safety", "powerfail", "last_on_state", "custom"]
    configured: bool | None = None
    on: HueModel | None = None
    dimming: HueModel | None = None
    color: HueModel | None = None


class PowerupEventState(HueModel):
    preset: Literal["safety", "powerfail", "last_on_state", "custom"] | None = None
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


class SignalingUpdate(HueRequest):
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


class LightMetadataUpdate(HueRequest):
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


class LightUpdate(HueRequest, LightStateMixin):
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


class GroupMetadataUpdate(HueRequest):
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


class GroupUpdate(HueRequest):
    metadata: GroupMetadataUpdate | GroupMetadata | None = None
    children: list[ResourceReference] | None = None


class GroupCreate(GroupUpdate):
    metadata: GroupMetadata
    children: list[ResourceReference] = Field(default_factory=list)


class GroupedLight(HueResource, LightStateMixin):
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


class SceneMetadataUpdate(HueRequest):
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


class SceneRecall(HueRequest):
    action: SceneAction = SceneAction.ACTIVE
    duration: int | None = Field(default=None, ge=0)
    dimming: DimmingState | None = None


class SceneUpdate(HueRequest):
    metadata: SceneMetadataUpdate | SceneMetadata | None = None
    actions: list[SceneActionTarget] | None = None
    palette: ScenePalette | None = None
    speed: float | None = Field(default=None, ge=0, le=1)
    auto_dynamic: bool | None = None
    recall: SceneRecall | None = None


class SceneCreate(HueRequest):
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


class SceneRecallRequest(HueRequest):
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


class EntertainmentConfigurationUpdate(HueRequest):
    action: StreamAction | None = None
    metadata: NamedMetadata | None = None
    configuration_type: EntertainmentConfigurationType | None = None
    stream_proxy: StreamProxy | None = None
