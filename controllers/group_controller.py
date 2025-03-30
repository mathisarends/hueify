from __future__ import annotations

from typing import Any, Dict, List, TypedDict

from bridge import HueBridge


class GroupState(TypedDict, total=False):
    on: bool
    bri: int
    hue: int
    sat: int
    xy: List[float]
    ct: int
    alert: str
    effect: str
    colormode: str
    any_on: bool
    all_on: bool


class GroupInfo(TypedDict):
    name: str
    lights: List[str]
    type: str
    state: GroupState
    recycle: bool
    class_: str
    action: Dict[str, Any]


class GroupController:
    """Controller for managing Philips Hue light groups."""
    
    def __init__(self, bridge: HueBridge) -> None:
        """Initialize the GroupController with a Hue Bridge.
        """
        self.bridge = bridge

    async def get_all_groups(self) -> Dict[str, GroupInfo]:
        """Retrieve all light groups from the Hue Bridge.
        """
        return await self.bridge.get_request("groups")

    async def set_group_state(self, group_id: str, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Update the state of a specific light group.
        """
        return await self.bridge.put_request(f"groups/{group_id}/action", state)

    async def set_group_brightness(self, group_id: str, brightness: int) -> List[Dict[str, Any]]:
        """Set the brightness level for a specific light group.
        """
        brightness = max(0, min(254, brightness))
        return await self.set_group_state(group_id, {"bri": brightness})

    async def get_active_group(self) -> str:
        """Find and return the ID of the first active light group.
        
        An active group is one that has at least one light turned on.
        Default group "0" is returned if no active groups are found.
        """
        groups = await self.get_all_groups()

        target_group = "0"

        for group_id, group_data in groups.items():
            if group_data.get("state", {}).get("any_on", False):
                target_group = group_id
                break

        return target_group