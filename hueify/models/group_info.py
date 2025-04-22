from typing import Any, Dict, List, Literal, Optional, TypedDict


class GroupState(TypedDict, total=False):
    """
    TypedDict representing the state of a Philips Hue light group.

    Attributes:
        on: Boolean indicating if the group is on
        bri: Brightness level (0-254)
        hue: Hue value (0-65535)
        sat: Saturation value (0-254)
        xy: CIE color space coordinates [x, y]
        ct: Color temperature in mireds (153-500)
        alert: Alert effect type ('none', 'select', 'lselect')
        effect: Effect type ('none', 'colorloop')
        colormode: Color mode ('hs', 'xy', 'ct')
        any_on: Boolean indicating if any light in the group is on
        all_on: Boolean indicating if all lights in the group are on
        transitiontime: Transition time in 100ms units (optional)
    """

    on: bool
    bri: int
    hue: int
    sat: int
    xy: List[float]
    ct: int
    alert: Literal["none", "select", "lselect"]
    effect: Literal["none", "colorloop"]
    colormode: Literal["hs", "xy", "ct"]
    any_on: bool
    all_on: bool
    transitiontime: Optional[int]


class GroupInfo(TypedDict):
    """
    TypedDict representing information about a Philips Hue light group.

    Attributes:
        name: Name of the group
        lights: List of light IDs in the group
        type: Type of the group
        state: Current state of the group
        recycle: Whether the group is marked for recycling
        class_: Class of the group
        action: Dictionary of actions applicable to the group
    """

    name: str
    lights: List[str]
    type: str
    state: GroupState
    recycle: bool
    class_: str
    action: Dict[str, Any]
