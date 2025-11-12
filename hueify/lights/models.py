from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field, TypeAdapter

from hueify.shared.types import LightOnState, ResourceReference


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


class LightDimmingState(BaseModel):
    brightness: float = Field(ge=0, le=100)
    min_dim_level: float = Field(default=0, ge=0, le=100)


class MirekSchema(BaseModel):
    mirek_minimum: int = Field(ge=50, le=1000)
    mirek_maximum: int = Field(ge=50, le=1000)


class ColorTemperatureState(BaseModel):
    mirek: int | None = Field(default=None, ge=50, le=1000)
    mirek_valid: bool = False
    mirek_schema: MirekSchema | None = None


class ColorXY(BaseModel):
    x: float = Field(ge=0, le=1)
    y: float = Field(ge=0, le=1)


class ColorGamut(BaseModel):
    red: ColorXY
    green: ColorXY
    blue: ColorXY


class GamutType(StrEnum):
    A = "A"
    B = "B"
    C = "C"
    OTHER = "other"


class ColorState(BaseModel):
    xy: ColorXY
    gamut: ColorGamut | None = None
    gamut_type: GamutType | None = None


class LightMetadata(BaseModel):
    name: str
    archetype: LightArchetype | None = None


class LightState(BaseModel):
    on: LightOnState | None = None
    dimming: LightDimmingState | None = None
    color_temperature: ColorTemperatureState | None = None
    color: ColorState | None = None


class LightInfo(BaseModel):
    id: UUID
    type: str
    owner: ResourceReference
    metadata: LightMetadata
    on: LightOnState | None = None
    dimming: LightDimmingState | None = None
    color_temperature: ColorTemperatureState | None = None
    color: ColorState | None = None


LightInfoListAdapter = TypeAdapter(list[LightInfo])
