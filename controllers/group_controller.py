from __future__ import annotations
from typing import Any, Dict, List, Literal, Optional, TypedDict
import asyncio
from bridge import HueBridge


class GroupState(TypedDict, total=False):
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
    name: str
    lights: List[str]
    type: str
    state: GroupState
    recycle: bool
    class_: str
    action: Dict[str, Any]


class GroupStateRepository:
    """Repository for storing and retrieving group states."""
    
    def __init__(self) -> None:
        self._saved_states: Dict[str, Dict[str, GroupState]] = {}
        self._last_off_state_id: Optional[str] = None
    
    @property
    def saved_states(self) -> Dict[str, Dict[str, GroupState]]:
        return self._saved_states.copy()
    
    def save_state(self, state_id: str, group_states: Dict[str, GroupState]) -> None:
        self._saved_states[state_id] = group_states.copy()
    
    def get_state(self, state_id: str) -> Optional[Dict[str, GroupState]]:
        return self._saved_states.get(state_id)
    
    def remove_state(self, state_id: str) -> bool:
        if state_id in self._saved_states:
            del self._saved_states[state_id]
            return True
        return False
    
    def set_last_off_state(self, state_id: str) -> None:
        self._last_off_state_id = state_id
    
    def get_last_off_state(self) -> Optional[str]:
        return self._last_off_state_id
    
    def clear_last_off_state(self) -> None:
        self._last_off_state_id = None


class GroupService:
    """Service for interacting with bridge APIs to control groups."""
    
    def __init__(self, bridge: HueBridge) -> None:
        self.bridge = bridge
    
    async def get_all_groups(self) -> Dict[str, GroupInfo]:
        return await self.bridge.get_request("groups")
    
    async def set_group_state(self, group_id: str, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        return await self.bridge.put_request(f"groups/{group_id}/action", state)
    
    async def get_group_state(self, group_id: str) -> GroupState:
        group_data = await self.bridge.get_request(f"groups/{group_id}")
        return group_data.get("state", {})


class GroupSwitch:
    """Handles turning groups on and off with state persistence."""
    
    def __init__(self, group_service: GroupService, state_repository: GroupStateRepository) -> None:
        self.group_service = group_service
        self.state_repository = state_repository
    
    async def turn_all_on(self, transition_time: int = 4) -> None:
        """Turn on all groups with a smooth transition, restoring previous state if available.
        """
        last_state_id = self.state_repository.get_last_off_state()
        saved_state = None
        
        if last_state_id:
            saved_state = self.state_repository.get_state(last_state_id)
        
        if saved_state:
            for group_id, state in saved_state.items():
                restore_state = self._get_restorable_state(state)
                # Add transition time to make the restoration smoother
                restore_state["transitiontime"] = transition_time
                await self.group_service.set_group_state(group_id, restore_state)
            
            self.state_repository.clear_last_off_state()
        else:
            # No saved state, just turn all groups on with transition
            groups = await self.group_service.get_all_groups()
            for group_id in groups:
                await self.group_service.set_group_state(group_id, {
                    "on": True,
                    "transitiontime": transition_time
                })
    
    async def turn_all_off(self, transition_time: int = 4) -> bool:
        """Turn off all groups with a smooth transition.
        """
        groups = await self.group_service.get_all_groups()
        group_ids = list(groups.keys())
        
        # Collect current states
        states: Dict[str, GroupState] = {}
        for group_id in group_ids:
            if group_id in groups:
                # For groups, we need to merge state and action properties
                group_state = groups[group_id]["state"].copy()
                group_action = groups[group_id]["action"].copy()
                # Action contains the light properties we want to save
                combined_state = {**group_state, **group_action}
                states[group_id] = combined_state
        
        # Save the states
        state_id = f"groups_before_off_{asyncio.get_event_loop().time()}"
        self.state_repository.save_state(state_id, states)
        self.state_repository.set_last_off_state(state_id)
        
        # Turn off all groups with a smooth transition
        for group_id in group_ids:
            await self.group_service.set_group_state(group_id, {
                "on": False,
                "transitiontime": transition_time
            })
            
        return True
    
    def _get_restorable_state(self, state: GroupState) -> Dict[str, Any]:
        """Extract restorable properties from a group state."""
        return {
            k: v
            for k, v in state.items()
            if k in ["on", "bri", "hue", "sat", "xy", "ct", "effect", "colormode"]
        }


class GroupController:
    """Controller for managing Philips Hue light groups with state persistence."""
    
    def __init__(self, bridge: HueBridge, group_name: Optional[str] = None) -> None:
        """Initialize the GroupController with a Hue Bridge and optional default group name.
        
        Args:
            bridge: HueBridge instance for API communication
            default_group_name: Name of the group to use by default
        """
        self.bridge = bridge
        self.state_repository = GroupStateRepository()
        self.group_service = GroupService(bridge)
        self.group_switch = GroupSwitch(self.group_service, self.state_repository)
        self.default_group_name = group_name
        self._group_name_to_id_cache: Dict[str, str] = {}
    
    async def get_all_groups(self) -> Dict[str, GroupInfo]:
        """Retrieve all light groups from the Hue Bridge."""
        return await self.group_service.get_all_groups()
    
    async def set_group_state(self, group_id_or_name: str, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Update the state of a specific light group.
        """
        group_id = await self._resolve_group_identifier(group_id_or_name)
        if not group_id:
            raise ValueError(f"Group '{group_id_or_name}' not found")
            
        return await self.group_service.set_group_state(group_id, state)
    
    async def set_group_brightness(self, group_id_or_name: str, brightness: int) -> List[Dict[str, Any]]:
        """Set the brightness level for a specific light group.
        """
        brightness = max(0, min(254, brightness))
        return await self.set_group_state(group_id_or_name, {"bri": brightness})
        
    async def _resolve_group_identifier(self, group_id_or_name: str) -> Optional[str]:
        """Resolve a group identifier to a group ID.
        """
        # Check if it's already a group ID
        groups = await self.get_all_groups()
        if group_id_or_name in groups:
            return group_id_or_name
            
        # Try to resolve as a name
        group_id = await self.get_group_id_by_name(group_id_or_name)
        if group_id:
            return group_id
            
        # If still not found and we have a default, use it
        if self.default_group_name:
            return await self.get_default_group_id()
            
        return None
    
    async def get_group_id_by_name(self, group_name: str) -> Optional[str]:
        """Find and return the group ID corresponding to the given name.
        
        Args:
            group_name: Name of the group to look for
            
        Returns:
            Group ID if found, None otherwise
        """
        # Check cache first
        if group_name in self._group_name_to_id_cache:
            return self._group_name_to_id_cache[group_name]
            
        # Cache miss, fetch from bridge
        groups = await self.get_all_groups()
        
        for group_id, group_data in groups.items():
            if group_data.get("name") == group_name:
                # Update cache
                self._group_name_to_id_cache[group_name] = group_id
                return group_id
                
        return None
    
    async def get_default_group_id(self) -> str:
        """Get the default group ID based on the configured default group name.
        
        If a default group name is set and found, its ID is returned.
        Otherwise, returns "0" (all lights).
        
        Returns:
            Group ID to use by default
        """
        if self.default_group_name:
            group_id = await self.get_group_id_by_name(self.default_group_name)
            if group_id:
                return group_id
                
        # Fallback to "0" (all lights group)
        return "0"
    
    async def get_active_group(self) -> str:
        """Find and return the ID of the first active light group.
        
        An active group is one that has at least one light turned on.
        If no active groups are found, returns the default group ID.
        """
        groups = await self.get_all_groups()

        # First check if the default group is active
        default_id = await self.get_default_group_id()
        if default_id in groups and groups[default_id].get("state", {}).get("any_on", False):
            return default_id

        # Otherwise find any active group
        for group_id, group_data in groups.items():
            if group_data.get("state", {}).get("any_on", False):
                return group_id

        # No active groups, return default
        return default_id
    
    async def turn_groups_on(self, transition_time: int = 4) -> bool:
        """Turn on all groups with a smooth transition, restoring previous state if available.
        
        Args:
            transition_time: Transition time in tenths of a second (default: 4 = 0.4 seconds)
                             The Hue API expects this value in 100ms units
        
        Returns:
            True if operation was successful
        """
        await self.group_switch.turn_all_on(transition_time)
        return True
    
    async def turn_groups_off(self, transition_time: int = 4) -> bool:
        """Turn off all groups with a smooth transition and save their current state.
        
        Args:
            transition_time: Transition time in tenths of a second (default: 4 = 0.4 seconds)
                             The Hue API expects this value in 100ms units
        
        Returns:
            True if operation was successful
        """
        return await self.group_switch.turn_all_off(transition_time)
    
    @property
    def saved_states(self) -> Dict[str, Dict[str, GroupState]]:
        """Get all saved group states."""
        return self.state_repository.saved_states
    
    async def save_group_states(self, group_identifiers: List[str], save_id: Optional[str] = None) -> str:
        """Save the current state of specified groups.
        
        Args:
            group_identifiers: List of group IDs or names
            save_id: Optional identifier for the saved state
            
        Returns:
            Identifier of the saved state
        """
        # Resolve all group identifiers to IDs
        group_ids = []
        for identifier in group_identifiers:
            group_id = await self._resolve_group_identifier(identifier)
            if group_id:
                group_ids.append(group_id)
        
        if not group_ids:
            raise ValueError("No valid groups found to save")
            
        if save_id is None:
            save_id = f"save_{'_'.join(group_ids)}"
            
        groups = await self.group_service.get_all_groups()
        states: Dict[str, GroupState] = {}
        
        for group_id in group_ids:
            if group_id in groups:
                # Combine state and action for complete state representation
                group_state = groups[group_id]["state"].copy()
                group_action = groups[group_id]["action"].copy()
                combined_state = {**group_state, **group_action}
                states[group_id] = combined_state
                
        self.state_repository.save_state(save_id, states)
        return save_id
        
    async def save_group_by_name(self, group_name: str, save_id: Optional[str] = None) -> str:
        """Convenience method to save a single group state by name.
        
        Args:
            group_name: Name of the group to save
            save_id: Optional identifier for the saved state
            
        Returns:
            Identifier of the saved state
        """
        group_id = await self.get_group_id_by_name(group_name)
        if not group_id:
            raise ValueError(f"Group '{group_name}' not found")
            
        return await self.save_group_states([group_id], save_id)
    
    async def restore_group_states(self, save_id: str, transition_time: int = 4) -> bool:
        """Restore previously saved group states with a smooth transition.
        
        Args:
            save_id: Identifier of the saved state to restore
            transition_time: Transition time in tenths of a second (default: 4 = 0.4 seconds)
                             The Hue API expects this value in 100ms units
        
        Returns:
            True if restoration was successful, False if the saved state wasn't found
        """
        saved_state = self.state_repository.get_state(save_id)
        if not saved_state:
            return False
            
        for group_id, state in saved_state.items():
            restore_state = {
                k: v
                for k, v in state.items()
                if k in ["on", "bri", "hue", "sat", "xy", "ct", "effect", "colormode"]
            }
            
            # Add transition time for a smoother change
            restore_state["transitiontime"] = transition_time
            
            await self.group_service.set_group_state(group_id, restore_state)
            
        return True
        
    def clear_saved_state(self, save_id: str) -> bool:
        """Remove a saved state from the repository."""
        return self.state_repository.remove_state(save_id)
    
    def get_saved_state(self, save_id: str) -> Optional[Dict[str, GroupState]]:
        """Retrieve a saved state from the repository."""
        return self.state_repository.get_state(save_id)