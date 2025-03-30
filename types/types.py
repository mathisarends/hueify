from enum import Enum
from typing import Any, Dict, List, Literal, Optional, TypedDict, Union

class ColorMode(str, Enum):
    HS = "hs"
    XY = "xy"
    CT = "ct"
    
class Effect(str, Enum):
    NONE = "none"
    COLORLOOP = "colorloop"

class AlertMode(str, Enum):
    NONE = "none"
    SELECT = "select"
    LSELECT = "lselect"

class LightStateDict(TypedDict, total=False):
    """Type definition for the state of a light"""
    on: bool
    bri: int  # 1-254
    hue: int  # 0-65535
    sat: int  # 0-254
    xy: List[float]  # [0-1, 0-1]
    ct: int  # 153-500 (Mired color temperature)
    effect: Literal["none", "colorloop"]
    colormode: Literal["hs", "xy", "ct"]
    alert: Literal["none", "select", "lselect"]
    transitiontime: Optional[int]  # in 100ms units
    reachable: bool  # read-only
    mode: str  # read-only

class LightInfoDict(TypedDict):
    """Type definition for light information"""
    state: LightStateDict
    type: str
    name: str
    modelid: str
    manufacturername: str
    productname: str
    uniqueid: str
    swversion: str
    swconfigid: str
    productid: str

class GroupStateDict(TypedDict, total=False):
    """Type definition for the state of a group"""
    all_on: bool
    any_on: bool

class GroupActionDict(TypedDict, total=False):
    """Type definition for group actions"""
    on: bool
    bri: int
    hue: int
    sat: int
    xy: List[float]
    ct: int
    effect: str
    colormode: str
    alert: str

class GroupInfoDict(TypedDict):
    """Type definition for group information"""
    name: str
    lights: List[str]
    type: str
    state: GroupStateDict
    action: GroupActionDict
    recycle: bool

class SceneInfoDict(TypedDict, total=False):
    """Type definition for scene information"""
    name: str
    type: str
    group: str
    lights: List[str]
    owner: str
    recycle: bool
    locked: bool
    appdata: Dict[str, Any]
    picture: str
    lastupdated: str
    version: int
    lightstates: Dict[str, LightStateDict]

class BridgeInfoDict(TypedDict):
    """Type definition for bridge information"""
    name: str
    datastoreversion: str
    swversion: str
    apiversion: str
    mac: str
    bridgeid: str
    factorynew: bool
    replacesbridgeid: Optional[str]
    modelid: str
    starterkitid: str
    
# Zone-related type definitions
class ZoneStateDict(TypedDict, total=False):
    """Type definition for the state of a zone"""
    all_on: bool
    any_on: bool

class ZoneActionDict(GroupActionDict):
    """Type definition for zone actions (inherits from group actions)"""
    # Inherits all the properties from GroupActionDict
    pass

class ZoneMetadataDict(TypedDict, total=False):
    """Type definition for zone metadata"""
    name: str
    archetype: str

class ZoneChildrenDict(TypedDict):
    """Type definition for zone children"""
    r: List[str]  # Resource identifiers

class ZonePositionDict(TypedDict):
    """Type definition for position information in a zone"""
    x: float
    y: float
    z: float

class ZoneMemberDict(TypedDict):
    """Type definition for a zone member (light position in zone)"""
    id: str
    position: ZonePositionDict
    service: Dict[str, str]
    metadata: Dict[str, Any]

class ZoneInfoDict(TypedDict):
    """Type definition for zone information"""
    id: str
    type: Literal["zone"]
    state: ZoneStateDict
    action: ZoneActionDict
    metadata: ZoneMetadataDict
    children: ZoneChildrenDict
    members: List[ZoneMemberDict]
    services: List[Dict[str, str]]

class ApiSuccessResponse(TypedDict):
    """Type definition for successful API responses"""
    success: Dict[str, Any]

class ApiErrorResponse(TypedDict):
    """Type definition for error API responses"""
    error: Dict[str, Any]

ApiResponse = Union[List[ApiSuccessResponse], List[ApiErrorResponse]]