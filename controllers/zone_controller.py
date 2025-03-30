from __future__ import annotations

from typing import Any, Dict, List, TypedDict

from bridge import HueBridge


class ZoneState(TypedDict, total=False):
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


class ZoneInfo(TypedDict):
    name: str
    lights: List[str]
    type: str
    state: ZoneState
    recycle: bool
    class_: str
    action: Dict[str, Any]


class ZoneController:
    """Controller for managing Philips Hue zones."""

    def __init__(self, bridge: HueBridge) -> None:
        """Initialize the ZoneController with a Hue Bridge."""
        self.bridge = bridge

    async def get_all_zones(self) -> Dict[str, ZoneInfo]:
        """Retrieve all zones from the Hue Bridge."""
        all_groups = await self.bridge.get_request("groups")
        return {
            group_id: group_data
            for group_id, group_data in all_groups.items()
            if group_data.get("type") == "Zone"
        }

    async def set_zone_state(self, zone_id: str, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Update the state of a specific zone."""
        return await self.bridge.put_request(f"groups/{zone_id}/action", state)

    async def set_zone_brightness(self, zone_id: str, brightness: int) -> List[Dict[str, Any]]:
        """Set the brightness level for a specific zone."""
        brightness = max(0, min(254, brightness))
        return await self.set_zone_state(zone_id, {"bri": brightness})

    async def get_active_zone(self) -> str:
        """Find and return the ID of the first active zone.
        
        An active zone is one that has at least one light turned on.
        Returns "0" if no active zones are found.
        """
        zones = await self.get_all_zones()

        for zone_id, zone_data in zones.items():
            if zone_data.get("state", {}).get("any_on", False):
                return zone_id

        return "0"
