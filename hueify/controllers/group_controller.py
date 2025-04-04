from __future__ import annotations
from typing import Any, Dict, List, Literal, Optional, TypedDict
import asyncio

from hueify.bridge import HueBridge
from hueify.controllers.group_scene_controller import GroupSceneController

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
        self._saved_states: Dict[str, GroupState] = {}
        self._last_off_state_id: Optional[str] = None
    
    @property
    def saved_states(self) -> Dict[str, GroupState]:
        return self._saved_states.copy()
    
    def save_state(self, state_id: str, group_state: GroupState) -> None:
        self._saved_states[state_id] = group_state.copy()
    
    def get_state(self, state_id: str) -> Optional[GroupState]:
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
    
    async def get_group(self, group_id: str) -> GroupInfo:
        return await self.bridge.get_request(f"groups/{group_id}")
    
    async def set_group_state(self, group_id: str, state: GroupState) -> List[Dict[str, Any]]:
        return await self.bridge.put_request(f"groups/{group_id}/action", state)
    
    async def get_group_id_by_name(self, group_name: str) -> Optional[str]:
        """Find and return the group ID corresponding to the given name."""
        groups = await self.get_all_groups()
        
        for group_id, group_data in groups.items():
            if group_data.get("name") == group_name:
                return group_id
                
        return None


class GroupControllerFactory:
    """Factory for creating GroupController instances."""
    
    def __init__(self, bridge: HueBridge) -> None:
        self.bridge = bridge
        self.group_service = GroupService(bridge)
        self._controllers_cache: Dict[str, GroupController] = {}
        self._groups_cache: Optional[Dict[str, GroupInfo]] = None
        
    async def get_cached_groups(self) -> Dict[str, GroupInfo]:
        """Get the current cached groups."""
        if not self._groups_cache:
            await self._refresh_groups_cache()
        return self._groups_cache.copy()
    
    async def get_controller(self, group_identifier: str) -> GroupController:
        """Returns an existing controller or creates a new one."""
        if group_identifier in self._controllers_cache:
            return self._controllers_cache[group_identifier]
        
        group_id = await self._resolve_group_identifier(group_identifier)
        
        if not group_id:
            available_groups = await self.get_available_groups_formatted()
            message = f"Group '{group_identifier}' not found.\n{available_groups}"
            raise ValueError(message)
        
        controller = GroupController(self.bridge, group_id)
        await controller.initialize()
        
        self._controllers_cache[group_id] = controller
        self._controllers_cache[controller.name] = controller
        
        return controller
    
    async def _resolve_group_identifier(self, identifier: str) -> Optional[str]:
        """Resolves the group ID from an identifier (name or ID)."""
        if not self._groups_cache:
            await self._refresh_groups_cache()
            
        if identifier in self._groups_cache:
            return identifier
        
        for group_id, group_data in self._groups_cache.items():
            if group_data.get("name") == identifier:
                return group_id
        
        identifier_lower = identifier.lower()
        for group_id, group_data in self._groups_cache.items():
            name = group_data.get("name", "")
            if name.lower() == identifier_lower:
                return group_id
                
        return None
    
    async def _refresh_groups_cache(self) -> None:
        """Refreshes the groups cache."""
        self._groups_cache = await self.group_service.get_all_groups()
    
    async def get_available_groups_formatted(self) -> str:
        """Returns a formatted overview of all available groups."""
        if not self._groups_cache:
            await self._refresh_groups_cache()
            
        groups_by_type: Dict[str, List[str]] = {}
        
        for _, info in self._groups_cache.items():
            group_type = info.get("type", "Unknown")
            group_name = info.get("name", "Unnamed")
            
            if group_type not in groups_by_type:
                groups_by_type[group_type] = []
            
            groups_by_type[group_type].append(group_name)
        
        for _, names in groups_by_type.items():
            names.sort()
        
        output = "Available groups:\n"
        
        for group_type, names in sorted(groups_by_type.items()):
            output += f"\n{group_type} groups:\n"
            for name in names:
                output += f"  - {name}\n"
                
        return output


class GroupController:
    """Controller for managing a specific Philips Hue light group."""
    NOT_INITIALIZED_ERROR_MSG = "Group controller not initialized. Call initialize() first."
    
    def __init__(self, bridge: HueBridge, group_identifier: str) -> None:
        """Initialize the GroupController with a Hue Bridge and a group.
        """
        self.bridge = bridge
        self.group_service = GroupService(bridge)
        self.state_repository = GroupStateRepository()
        self.group_identifier = group_identifier
        self._group_id: Optional[str] = None
        self._group_info: Optional[GroupInfo] = None
        
        self._scene_controller: Optional[GroupSceneController] = None
    
    async def initialize(self) -> None:
        """Initialize the controller by resolving the group ID."""
        group_id = await self._resolve_group_identifier(self.group_identifier)
        if not group_id:
            raise ValueError(f"Group '{self.group_identifier}' not found")
        
        self._group_id = group_id
        await self._refresh_group_info()
    
    async def _resolve_group_identifier(self, identifier: str) -> Optional[str]:
        """Resolve a group identifier to a group ID."""
        groups = await self.group_service.get_all_groups()
        if identifier in groups:
            return identifier
            
        return await self.group_service.get_group_id_by_name(identifier)
    
    async def _refresh_group_info(self) -> None:
        """Refresh the cached group information."""
        if not self._group_id:
            await self.initialize()
            
        self._group_info = await self.group_service.get_group(self._group_id)
    
    @property
    def group_id(self) -> str:
        """Get the ID of the controlled group."""
        if not self._group_id:
            raise RuntimeError(GroupController.NOT_INITIALIZED_ERROR_MSG)
        return self._group_id
    
    @property
    def name(self) -> str:
        """Get the name of the controlled group."""
        if not self._group_info:
            raise RuntimeError(GroupController.NOT_INITIALIZED_ERROR_MSG)
        return self._group_info.get("name", "")
    
    
    @property
    def state(self) -> GroupState:
        """Get the current state of the group."""
        if not self._group_info:
            raise RuntimeError(GroupController.NOT_INITIALIZED_ERROR_MSG)
        
        group_state = self._group_info.get("state", {}).copy()
        group_action = self._group_info.get("action", {}).copy()
        return {**group_state, **group_action}
    
    @property
    def scenes(self) -> GroupSceneController:
        """
        Get the scene controller for this group.
        """
        if not self._group_id:
            raise RuntimeError(GroupController.NOT_INITIALIZED_ERROR_MSG)
            
        if not self._scene_controller:
            self._scene_controller = GroupSceneController(self.bridge, self._group_id)
            
        return self._scene_controller
    
    async def activate_scene(self, scene_name: str) -> List[Dict[str, Any]]:
        """
        Convenience method to activate a scene by name.
        """
        return await self.scenes.activate_scene_by_name(scene_name)
    
    async def set_state(self, state: GroupState, transition_time: Optional[int] = None) -> List[Dict[str, Any]]:
        """Update the state of this group.
        """
        if transition_time is not None:
            state = state.copy()
            state["transitiontime"] = transition_time
            
        result = await self.group_service.set_group_state(self.group_id, state)
        
        await self._refresh_group_info()
        return result
    
    async def get_current_brightness_percentage(self) -> int:
        """Returns the current brightness as a percentage value (0-100)."""
        await self._refresh_group_info()
        current_state = self.state
        
        if not current_state.get("on", False):
            return 0
        
        current_brightness = current_state.get("bri", 0)
        return round(current_brightness * 100 / 254)
        
    async def set_brightness_percentage(self, percentage: int, transition_time: Optional[int] = None) -> List[Dict[str, Any]]:
        """Sets the brightness of the group to a percentage value.
        
        Args:
            percentage: Brightness in percent (0-100)
            transition_time: Transition time in 100ms units
        """
        percentage = max(0, min(100, percentage))
        
        if percentage == 0:
            return await self.turn_off(transition_time if transition_time is not None else 4)
        
        # Convert from percent (0-100) to Hue brightness (0-254)
        brightness = round(percentage * 254 / 100)
        
        state: GroupState = {"on": True, "bri": brightness}
        return await self.set_state(state, transition_time)
    
    
    async def increase_brightness_percentage(self, increment: int = 10, transition_time: int = 4) -> List[Dict[str, Any]]:
        """Increases the brightness of the group by the specified percentage.
        """
        current_percentage = await self.get_current_brightness_percentage()
        
        if current_percentage == 0:
            return await self.set_brightness_percentage(min(increment, 100), transition_time)
        
        new_percentage = min(current_percentage + increment, 100)
        
        return await self.set_brightness_percentage(new_percentage, transition_time)

    async def decrease_brightness_percentage(self, decrement: int = 10, transition_time: int = 4) -> List[Dict[str, Any]]:
        """Decreases the brightness of the group by the specified percentage.
        """
        current_percentage = await self.get_current_brightness_percentage()
        
        if current_percentage == 0:
            return []
        
        new_percentage = max(current_percentage - decrement, 0)
        
        if new_percentage <= 2:
            return await self.turn_off(transition_time)
        
        return await self.set_brightness_percentage(new_percentage, transition_time)
    
    
    async def turn_on(self, transition_time: int = 4) -> List[Dict[str, Any]]:
        """Turn on this group with a smooth transition, restoring previous state if available.
        """
        last_state_id = self.state_repository.get_last_off_state()
        saved_state = None
        
        if last_state_id:
            saved_state = self.state_repository.get_state(last_state_id)
        
        if saved_state:
            restore_state: GroupState = {
                k: v
                for k, v in saved_state.items()
                if k in ["on", "bri", "hue", "sat", "xy", "ct", "effect", "colormode"]
            }
            
            restore_state["transitiontime"] = transition_time
            
            result = await self.set_state(restore_state)
            self.state_repository.clear_last_off_state()
            return result
        else:
            # No saved state, just turn on
            state: GroupState = {"on": True}
            return await self.set_state(state, transition_time)
    
    async def turn_off(self, transition_time: int = 4) -> List[Dict[str, Any]]:
        await self._refresh_group_info()
        
        # Save the current state
        current_state = self.state
        state_id = f"group_{self.group_id}_before_off_{asyncio.get_event_loop().time()}"
        self.state_repository.save_state(state_id, current_state)
        self.state_repository.set_last_off_state(state_id)
        
        state: GroupState = {"on": False}
        return await self.set_state(state, transition_time)
    
    async def save_state(self, save_id: Optional[str] = None) -> str:
        """Save the current state of this group.
        """
        await self._refresh_group_info()
        
        if save_id is None:
            save_id = f"save_group_{self.group_id}_{asyncio.get_event_loop().time()}"
            
        self.state_repository.save_state(save_id, self.state)
        return save_id
    
    async def restore_state(self, save_id: str, transition_time: int = 4) -> bool:
        """Restore a previously saved state with a smooth transition.
        """
        saved_state = self.state_repository.get_state(save_id)
        if not saved_state:
            return False
            
        restore_state: GroupState = {
            k: v
            for k, v in saved_state.items()
            if k in ["on", "bri", "hue", "sat", "xy", "ct", "effect", "colormode"]
        }
        
        restore_state["transitiontime"] = transition_time
        
        await self.set_state(restore_state)
        return True
    
    def clear_saved_state(self, save_id: str) -> bool:
        """Remove a saved state from the repository."""
        return self.state_repository.remove_state(save_id)
    
    def get_saved_state(self, save_id: str) -> Optional[GroupState]:
        """Retrieve a saved state from the repository."""
        return self.state_repository.get_state(save_id)
    
    @property
    def saved_states(self) -> Dict[str, GroupState]:
        """Get all saved states for this group."""
        return self.state_repository.saved_states
    
    async def is_any_on(self) -> bool:
        """Check if any lights in the group are on."""
        await self._refresh_group_info()
        return self._group_info.get("state", {}).get("any_on", False)
    
    async def is_all_on(self) -> bool:
        """Check if all lights in the group are on."""
        await self._refresh_group_info()
        return self._group_info.get("state", {}).get("all_on", False)


class GroupsManager:
    """Manager for all Philips Hue light groups."""
    
    def __init__(self, bridge: HueBridge) -> None:
        """Initialize the GroupsManager with a Hue Bridge."""
        self.bridge = bridge
        self.group_service = GroupService(bridge)
        self.controller_factory = GroupControllerFactory(bridge)
    
    async def get_all_groups(self) -> Dict[str, GroupInfo]:
        """Retrieve all light groups from the Hue Bridge."""
        return await self.controller_factory.get_cached_groups()
    
    async def get_controller(self, group_identifier: str) -> GroupController:
        """Get a controller for the specified group."""
        return await self.controller_factory.get_controller(group_identifier)
    
    async def get_available_groups_formatted(self) -> str:
        """Get a formatted overview of all available groups."""
        return await self.controller_factory.get_available_groups_formatted()