from __future__ import annotations
import random
from typing import Any, Dict, List, Literal, Optional, TypedDict
import asyncio

from rapidfuzz import process

from hueify.bridge import HueBridge
from hueify.controllers.group_scene_controller import GroupSceneController


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


class GroupStateRepository:
    """
    Repository for storing and retrieving group states.

    This class provides methods to save, retrieve, and manage light group states,
    enabling features like state restoration when turning lights back on.
    """

    def __init__(self) -> None:
        """
        Initialize an empty group state repository.
        """
        self._saved_states: Dict[str, GroupState] = {}
        self._last_off_state_id: Optional[str] = None

    @property
    def saved_states(self) -> Dict[str, GroupState]:
        """
        Get a copy of all saved states.

        Returns:
            A dictionary mapping state IDs to their corresponding group states
        """
        return self._saved_states.copy()

    def save_state(self, state_id: str, group_state: GroupState) -> None:
        """
        Save a group state with the specified ID.

        Args:
            state_id: Unique identifier for the state
            group_state: The group state to save
        """
        self._saved_states[state_id] = group_state.copy()

    def get_state(self, state_id: str) -> Optional[GroupState]:
        """
        Retrieve a saved state by its ID.

        Args:
            state_id: ID of the state to retrieve

        Returns:
            The saved state if found, None otherwise
        """
        return self._saved_states.get(state_id)

    def remove_state(self, state_id: str) -> bool:
        """
        Remove a saved state by its ID.

        Args:
            state_id: ID of the state to remove

        Returns:
            True if the state was found and removed, False otherwise
        """
        if state_id in self._saved_states:
            del self._saved_states[state_id]
            return True
        return False

    def set_last_off_state(self, state_id: str) -> None:
        """
        Set the ID of the last saved state before turning off.

        Args:
            state_id: ID of the state to set as the last off state
        """
        self._last_off_state_id = state_id

    def get_last_off_state(self) -> Optional[str]:
        """
        Get the ID of the last saved state before turning off.

        Returns:
            The ID of the last off state if available, None otherwise
        """
        return self._last_off_state_id

    def clear_last_off_state(self) -> None:
        """
        Clear the stored last off state ID.
        """
        self._last_off_state_id = None


class GroupService:
    """
    Service for interacting with the Philips Hue bridge API to control groups.

    This class provides methods to get information about groups and modify
    their states through the bridge API.
    """

    def __init__(self, bridge: HueBridge) -> None:
        """
        Initialize the GroupService with a Hue Bridge.

        Args:
            bridge: The HueBridge instance to use for API requests
        """
        self.bridge = bridge

    async def get_all_groups(self) -> Dict[str, GroupInfo]:
        """
        Retrieve all groups from the Hue Bridge.

        Returns:
            A dictionary mapping group IDs to their corresponding group information
        """
        return await self.bridge.get_request("groups")

    async def get_group(self, group_id: str) -> GroupInfo:
        """
        Retrieve information about a specific group.

        Args:
            group_id: ID of the group to retrieve

        Returns:
            Group information for the specified ID
        """
        return await self.bridge.get_request(f"groups/{group_id}")

    async def set_group_state(self, group_id: str, state: GroupState) -> List[Dict[str, Any]]:
        """
        Set the state of a specific group with improved handling.
        
        Args:
            group_id: ID of the group to modify
            state: The state to apply to the group
            
        Returns:
            A list of responses from the Hue Bridge API
        """
        # Kopiere den Zustand, um das Original nicht zu verändern
        state_copy = state.copy()
        
        # Prüfe, ob ein 'on'-Status festgelegt wurde
        explicit_on_state = "on" in state_copy
        on_state = state_copy.pop("on", True) if explicit_on_state else True
        
        results = []
        
        # Wenn andere Zustandsänderungen vorhanden sind, wende sie an
        if state_copy:
            results.append(await self.bridge.put_request(f"groups/{group_id}/action", state_copy))
        
        # Wenn der on-Status explizit gesetzt werden soll, tue dies in einem separaten Aufruf
        if explicit_on_state:
            results.append(await self.bridge.put_request(f"groups/{group_id}/action", {"on": on_state}))
        
        return results

    async def get_group_id_by_name(self, group_name: str) -> Optional[str]:
        """
        Find and return the group ID corresponding to the given name.

        Args:
            group_name: Name of the group to find

        Returns:
            The group ID if found, None otherwise
        """
        groups = await self.get_all_groups()

        for group_id, group_data in groups.items():
            if group_data.get("name") == group_name:
                return group_id

        return None


class GroupControllerFactory:
    """
    Factory for creating and managing GroupController instances.

    This class provides methods to create and retrieve group controllers,
    with caching to avoid creating duplicate controllers for the same group.
    """

    def __init__(self, bridge: HueBridge) -> None:
        """
        Initialize the GroupControllerFactory with a Hue Bridge.

        Args:
            bridge: The HueBridge instance to use for creating controllers
        """
        self.bridge = bridge
        self.group_service = GroupService(bridge)
        self._controllers_cache: Dict[str, GroupController] = {}
        self._groups_cache: Optional[Dict[str, GroupInfo]] = None

    async def get_cached_groups(self) -> Dict[str, GroupInfo]:
        """
        Get the current cached groups, refreshing the cache if necessary.

        Returns:
            A dictionary mapping group IDs to their corresponding group information
        """
        if not self._groups_cache:
            await self._refresh_groups_cache()
        return self._groups_cache.copy()

    async def _resolve_group_identifier(self, identifier: str) -> Optional[str]:
        """
        Resolves the group ID from an identifier (name or ID).

        Args:
            identifier: Name or ID of the group

        Returns:
            The group ID if found, None otherwise
        """
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
        """
        Refreshes the groups cache by fetching the latest groups from the bridge.
        """
        self._groups_cache = await self.group_service.get_all_groups()

    async def get_available_groups_formatted(self) -> str:
        """
        Returns a formatted overview of all available groups, organized by type.

        Returns:
            A formatted string with group information
        """
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

    async def _find_closest_group_name(self, query: str) -> Optional[str]:
        """
        Find the closest matching group name using fuzzy matching.

        Args:
            query: The group name to search for

        Returns:
            The closest matching group name if similarity > 75, None otherwise
        """
        if not self._groups_cache:
            await self._refresh_groups_cache()

        group_names = []
        for _, group_data in self._groups_cache.items():
            name = group_data.get("name", "")
            if name:
                group_names.append(name)

        if not group_names:
            return None

        result = process.extractOne(query, group_names)

        if len(result) >= 2:
            best_match = result[0]
            score = result[1]

            if score > 75:
                return best_match

        return None

    async def get_controller(self, group_identifier: str) -> GroupController:
        """
        Returns an existing controller or creates a new one for the specified group.
        Uses fuzzy matching if an exact match is not found.

        Args:
            group_identifier: Name or ID of the group

        Returns:
            A GroupController instance for the specified group

        Raises:
            ValueError: If the group identifier cannot be resolved to a valid group
        """
        if group_identifier in self._controllers_cache:
            return self._controllers_cache[group_identifier]

        group_id = await self._resolve_group_identifier(group_identifier)

        if not group_id:
            fuzzy_match = await self._find_closest_group_name(group_identifier)
            if fuzzy_match:
                return await self.get_controller(fuzzy_match)

            available_groups = await self.get_available_groups_formatted()
            message = f"Group '{group_identifier}' not found.\n{available_groups}"
            raise ValueError(message)

        controller = GroupController(self.bridge, group_id)
        await controller.initialize()

        self._controllers_cache[group_id] = controller
        self._controllers_cache[controller.name] = controller

        return controller


class GroupController:
    """
    Controller for managing a specific Philips Hue light group.

    This class provides methods to control and manage a specific light group,
    including turning it on/off, adjusting brightness, saving and restoring states,
    and accessing scene functionality.
    """

    NOT_INITIALIZED_ERROR_MSG = (
        "Group controller not initialized. Call initialize() first."
    )

    def __init__(self, bridge: HueBridge, group_identifier: str) -> None:
        """
        Initialize the GroupController with a Hue Bridge and a group identifier.

        Args:
            bridge: The HueBridge instance to use for API requests
            group_identifier: Name or ID of the group to control
        """
        self.bridge = bridge
        self.group_service = GroupService(bridge)
        self.state_repository = GroupStateRepository()
        self.group_identifier = group_identifier
        self._group_id: Optional[str] = None
        self._group_info: Optional[GroupInfo] = None

        self._scene_controller: Optional[GroupSceneController] = None

    async def initialize(self) -> None:
        """
        Initialize the controller by resolving the group ID and loading initial info.

        Raises:
            ValueError: If the group identifier cannot be resolved to a valid group
        """
        group_id = await self._resolve_group_identifier(self.group_identifier)
        if not group_id:
            raise ValueError(f"Group '{self.group_identifier}' not found")

        self._group_id = group_id
        await self._refresh_group_info()

    async def _resolve_group_identifier(self, identifier: str) -> Optional[str]:
        """
        Resolve a group identifier to a group ID.

        Args:
            identifier: Name or ID of the group

        Returns:
            The group ID if found, None otherwise
        """
        groups = await self.group_service.get_all_groups()
        if identifier in groups:
            return identifier

        return await self.group_service.get_group_id_by_name(identifier)

    async def _refresh_group_info(self) -> None:
        """
        Refresh the cached group information from the bridge.
        """
        if not self._group_id:
            await self.initialize()

        self._group_info = await self.group_service.get_group(self._group_id)

    @property
    def group_id(self) -> str:
        """
        Get the ID of the controlled group.

        Returns:
            The group ID

        Raises:
            RuntimeError: If the controller is not initialized
        """
        if not self._group_id:
            raise RuntimeError(GroupController.NOT_INITIALIZED_ERROR_MSG)
        return self._group_id

    @property
    def name(self) -> str:
        """
        Get the name of the controlled group.

        Returns:
            The group name

        Raises:
            RuntimeError: If the controller is not initialized
        """
        if not self._group_info:
            raise RuntimeError(GroupController.NOT_INITIALIZED_ERROR_MSG)
        return self._group_info.get("name", "")

    @property
    def state(self) -> GroupState:
        """
        Get the current state of the group.

        Returns:
            The current group state

        Raises:
            RuntimeError: If the controller is not initialized
        """
        if not self._group_info:
            raise RuntimeError(GroupController.NOT_INITIALIZED_ERROR_MSG)

        group_state = self._group_info.get("state", {}).copy()
        group_action = self._group_info.get("action", {}).copy()
        return {**group_state, **group_action}

    @property
    def scene_controller(self) -> GroupSceneController:
        """
        Get the scene controller for this group.

        Returns:
            A GroupSceneController instance for this group

        Raises:
            RuntimeError: If the controller is not initialized
        """
        if not self._group_id:
            raise RuntimeError(GroupController.NOT_INITIALIZED_ERROR_MSG)

        if not self._scene_controller:
            self._scene_controller = GroupSceneController(self.bridge, self._group_id)

        return self._scene_controller

    async def activate_scene(self, scene_name: str) -> List[Dict[str, Any]]:
        """
        Convenience method to activate a scene by name.

        Args:
            scene_name: Name of the scene to activate

        Returns:
            A list of responses from the Hue Bridge API
        """
        return await self.scene_controller.activate_scene_by_name(scene_name)

    async def set_state(
        self, state: GroupState, transition_time: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Update the state of this group.

        Args:
            state: The state to apply to the group
            transition_time: Transition time in 100ms units (optional)

        Returns:
            A list of responses from the Hue Bridge API
        """
        if transition_time is not None:
            state = state.copy()
            state["transitiontime"] = transition_time

        result = await self.group_service.set_group_state(self.group_id, state)

        await self._refresh_group_info()
        return result

    async def get_current_brightness_percentage(self) -> int:
        """
        Returns the current brightness as a percentage value (0-100).

        Returns:
            The current brightness percentage
        """
        await self._refresh_group_info()
        current_state = self.state

        if not current_state.get("on", False):
            return 0

        current_brightness = current_state.get("bri", 0)
        return round(current_brightness * 100 / 254)

    async def set_brightness_percentage(
        self, percentage: int, transition_time: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Sets the brightness of the group to a percentage value.

        Args:
            percentage: Brightness in percent (0-100)
            transition_time: Transition time in 100ms units

        Returns:
            A list of responses from the Hue Bridge API
        """
        percentage = max(0, min(100, percentage))

        if percentage == 0:
            return await self.turn_off(
                transition_time if transition_time is not None else 4
            )

        # Convert from percent (0-100) to Hue brightness (0-254)
        brightness = round(percentage * 254 / 100)

        state: GroupState = {"on": True, "bri": brightness}
        return await self.set_state(state, transition_time)

    async def increase_brightness_percentage(
        self, increment: int = 10, transition_time: int = 4
    ) -> List[Dict[str, Any]]:
        """
        Increases the brightness of the group by the specified percentage.

        Args:
            increment: Percentage to increase brightness by (default: 10)
            transition_time: Transition time in 100ms units (default: 4)

        Returns:
            A list of responses from the Hue Bridge API
        """
        current_percentage = await self.get_current_brightness_percentage()

        if current_percentage == 0:
            return await self.set_brightness_percentage(
                min(increment, 100), transition_time
            )

        new_percentage = min(current_percentage + increment, 100)

        return await self.set_brightness_percentage(new_percentage, transition_time)

    async def decrease_brightness_percentage(
        self, decrement: int = 10, transition_time: int = 4
    ) -> List[Dict[str, Any]]:
        """
        Decreases the brightness of the group by the specified percentage.

        Args:
            decrement: Percentage to decrease brightness by (default: 10)
            transition_time: Transition time in 100ms units (default: 4)

        Returns:
            A list of responses from the Hue Bridge API
        """
        current_percentage = await self.get_current_brightness_percentage()

        if current_percentage == 0:
            return []

        new_percentage = max(current_percentage - decrement, 0)

        if new_percentage <= 2:
            return await self.turn_off(transition_time)

        return await self.set_brightness_percentage(new_percentage, transition_time)

    async def turn_on(self, transition_time: int = 4) -> List[Dict[str, Any]]:
        """
        Turn on this group with a smooth transition, restoring previous state if available.

        Args:
            transition_time: Transition time in 100ms units (default: 4)

        Returns:
            A list of responses from the Hue Bridge API
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

        state: GroupState = {"on": True}
        return await self.set_state(state, transition_time)

    async def turn_off(self, transition_time: int = 4) -> List[Dict[str, Any]]:
        """
        Turn off this group with a smooth transition, saving the current state.

        Args:
            transition_time: Transition time in 100ms units (default: 4)

        Returns:
            A list of responses from the Hue Bridge API
        """
        await self._refresh_group_info()

        # Save the current state
        current_state = self.state
        state_id = f"group_{self.group_id}_before_off_{asyncio.get_event_loop().time()}"
        self.state_repository.save_state(state_id, current_state)
        self.state_repository.set_last_off_state(state_id)

        state: GroupState = {"on": False}
        return await self.set_state(state, transition_time)

    async def save_state(self, save_id: Optional[str] = None) -> str:
        """
        Save the current state of this group.

        Args:
            save_id: ID to use for the saved state (generated if None)

        Returns:
            The ID of the saved state
        """
        await self._refresh_group_info()

        if save_id is None:
            save_id = f"save_group_{self.group_id}_{asyncio.get_event_loop().time()}"

        self.state_repository.save_state(save_id, self.state)
        return save_id

    async def restore_state(self, save_id: str, transition_time: int = 4) -> bool:
        """
        Restore a previously saved state with a smooth transition.

        Args:
            save_id: ID of the state to restore
            transition_time: Transition time in 100ms units (default: 4)

        Returns:
            True if the state was restored successfully, False otherwise
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
        """
        Remove a saved state from the repository.

        Args:
            save_id: ID of the state to remove

        Returns:
            True if the state was found and removed, False otherwise
        """
        return self.state_repository.remove_state(save_id)

    def get_saved_state(self, save_id: str) -> Optional[GroupState]:
        """
        Retrieve a saved state from the repository.

        Args:
            save_id: ID of the state to retrieve

        Returns:
            The saved state if found, None otherwise
        """
        return self.state_repository.get_state(save_id)

    @property
    def saved_states(self) -> Dict[str, GroupState]:
        """
        Get all saved states for this group.

        Returns:
            A dictionary mapping state IDs to their corresponding group states
        """
        return self.state_repository.saved_states
    
    # TODO: Das soll hier das Standardverhalten von State sein.
    async def subtle_individual_light_changes(self, 
                                           base_hue_shift: int = 1000,
                                           hue_variation: int = 500,
                                           sat_adjustment: int = 0,
                                           sat_variation: int = 10,
                                           transition_time: int = 10) -> str:
        """
        Creates subtle and varied color changes to individual lights in the group
        without affecting their brightness.
        
        Args:
            base_hue_shift: Base amount to shift hue values (default: 1000)
            hue_variation: Random variation to add/subtract from base_hue_shift (default: 500)
            sat_adjustment: Base amount to adjust saturation (default: 0)
            sat_variation: Random variation to add/subtract from sat_adjustment (default: 10)
            transition_time: Transition time in 100ms units (default: 10)
            
        Returns:
            The ID of the saved state for this color change operation
        """
        current_group_state = self.state
        state_id = f"individual_color_{self.group_id}_{int(asyncio.get_event_loop().time())}"
        self.state_repository.save_state(state_id, current_group_state)
        
        light_ids = await self.get_lights_in_group()
        
        individual_light_states = {}
        
        for light_id in light_ids:
            light_state = await self.get_light_state(light_id)
            
            individual_light_states[light_id] = light_state
            
            if not light_state.get("on", False):
                continue
            
            new_light_state = {"on": True}
            
            if "hue" in light_state:
                individual_hue_shift = base_hue_shift + random.randint(-hue_variation, hue_variation)
                new_light_state["hue"] = (light_state["hue"] + individual_hue_shift) % 65536
            
            if "sat" in light_state and (sat_adjustment != 0 or sat_variation != 0):
                individual_sat_adjustment = sat_adjustment + random.randint(-sat_variation, sat_variation)
                new_light_state["sat"] = max(0, min(254, light_state["sat"] + individual_sat_adjustment))
            
            if "colormode" in light_state:
                new_light_state["colormode"] = light_state["colormode"]
            
            new_light_state["transitiontime"] = transition_time
            
            await self.set_light_state(light_id, new_light_state)
        
        special_key = f"{state_id}_individual_lights"
        self.state_repository.save_state(special_key, {"light_states": individual_light_states})
        
        return state_id
    
    async def restore_individual_light_states(self, state_id: str, transition_time: int = 4) -> bool:
        """
        Restore previously saved individual light states.
        
        Args:
            state_id: ID of the state to restore
            transition_time: Transition time in 100ms units (default: 4)
            
        Returns:
            True if states were restored successfully, False otherwise
        """
        # Check if this was an individual light state save
        special_key = f"{state_id}_individual_lights"
        individual_states = self.state_repository.get_state(special_key)
        
        if individual_states and "light_states" in individual_states:
            light_states = individual_states["light_states"]
            
            for light_id, original_state in light_states.items():
                # Extract only the color-related properties for restoration
                restore_state = {
                    k: v for k, v in original_state.items()
                    if k in ["on", "bri", "hue", "sat", "xy", "ct", "effect", "colormode"]
                }
                
                # Apply transition time
                restore_state["transitiontime"] = transition_time
                
                # Apply original state to this light
                await self.set_light_state(light_id, restore_state)
                
            return True
        
        return await self.restore_state(state_id, transition_time)
    
    async def get_lights_in_group(self) -> List[str]:
        """
        Get a list of light IDs that belong to this group.
        
        Returns:
            List of light IDs in the group
        """
        await self._refresh_group_info()
        if not self._group_info:
            raise RuntimeError(self.NOT_INITIALIZED_ERROR_MSG)
        
        return self._group_info.get("lights", [])
    
    async def get_light_state(self, light_id: str) -> Dict[str, Any]:
        """
        Get the current state of a specific light.
        
        Args:
            light_id: ID of the light
            
        Returns:
            The current state of the light
        """
        light_info = await self.bridge.get_request(f"lights/{light_id}")
        return light_info.get("state", {})
    
    async def set_light_state(self, light_id: str, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Set the state of a specific light.
        
        Args:
            light_id: ID of the light
            state: The state to apply to the light
            
        Returns:
            Response from the Hue Bridge API
        """
        return await self.bridge.put_request(f"lights/{light_id}/state", state)


class GroupsManager:
    """
    Manager for all Philips Hue light groups.

    This class provides methods to retrieve information about all available groups
    and get controllers for specific groups.
    """

    def __init__(self, bridge: HueBridge) -> None:
        """
        Initialize the GroupsManager with a Hue Bridge.

        Args:
            bridge: The HueBridge instance to use for API requests
        """
        self.bridge = bridge
        self.group_service = GroupService(bridge)
        self.controller_factory = GroupControllerFactory(bridge)

    async def get_all_groups(self) -> Dict[str, GroupInfo]:
        """
        Retrieve all light groups from the Hue Bridge.

        Returns:
            A dictionary mapping group IDs to their corresponding group information
        """
        return await self.controller_factory.get_cached_groups()

    async def get_controller(self, group_identifier: str) -> GroupController:
        """
        Get a controller for the specified group.

        Args:
            group_identifier: Name or ID of the group

        Returns:
            A GroupController instance for the specified group

        Raises:
            ValueError: If the group identifier cannot be resolved to a valid group
        """
        return await self.controller_factory.get_controller(group_identifier)

    async def get_available_groups_formatted(self) -> str:
        """
        Get a formatted overview of all available groups.

        Returns:
            A formatted string with group information
        """
        return await self.controller_factory.get_available_groups_formatted()