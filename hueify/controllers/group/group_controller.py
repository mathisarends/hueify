from __future__ import annotations
import random
from typing import Any, Dict, List, Optional
import asyncio

from hueify.bridge import HueBridge
from hueify.controllers.group.group_state_repository import (
    GroupService,
    GroupStateRepository,
)
from hueify.controllers.group_scene_controller import GroupSceneController
from hueify.models.group_info import GroupInfo, GroupState


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
        """
        group_id = await self._resolve_group_identifier(self.group_identifier)
        if not group_id:
            raise ValueError(f"Group '{self.group_identifier}' not found")

        self._group_id = group_id
        await self._refresh_group_info()

    async def _resolve_group_identifier(self, identifier: str) -> Optional[str]:
        """
        Resolve a group identifier to a group ID.
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
        """
        if not self._group_id:
            raise RuntimeError(GroupController.NOT_INITIALIZED_ERROR_MSG)
        return self._group_id

    @property
    def name(self) -> str:
        """
        Get the name of the controlled group.
        """
        if not self._group_info:
            raise RuntimeError(GroupController.NOT_INITIALIZED_ERROR_MSG)
        return self._group_info.get("name", "")

    @property
    def state(self) -> GroupState:
        """
        Get the current state of the group.
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
        return await self.scene_controller.activate_scene_by_name(scene_name)

    async def set_state(
        self, state: GroupState, transition_time: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Update the state of this group.
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
        """
        last_state_id = self.state_repository.get_last_off_state()

        if last_state_id:
            success = await self.restore_state(last_state_id, transition_time)

            if success:
                self.state_repository.clear_last_off_state()
                return []

        state: GroupState = {"on": True}
        return await self.set_state(state, transition_time)

    async def turn_off(self, transition_time: int = 4) -> List[Dict[str, Any]]:
        """
        Turn off this group with a smooth transition, saving the current state.
        """
        state_id = await self.save_state()
        self.state_repository.set_last_off_state(state_id)

        state: GroupState = {"on": False}
        return await self.set_state(state, transition_time)

    async def save_state(self, save_id: Optional[str] = None) -> str:
        """
        Save the current state of this group, including individual light states.
        """
        await self._refresh_group_info()

        if save_id is None:
            save_id = f"save_group_{self.group_id}_{asyncio.get_event_loop().time()}"

        self.state_repository.save_state(save_id, self.state)

        light_ids = await self.get_lights_in_group()
        individual_light_states = {}

        for light_id in light_ids:
            light_state = await self.get_light_state(light_id)
            individual_light_states[light_id] = light_state

        self.state_repository.save_state(
            save_id,
            {"group_state": self.state, "light_states": individual_light_states},
        )

        return save_id

    async def restore_state(
        self, save_id: str, transition_time_seconds: float = 0.4
    ) -> bool:
        """
        Restore a previously saved state with a smooth transition.
        This method will first try to restore individual light states,
        and if not available, will fall back to group state restoration.
        """
        saved_state = self.state_repository.get_state(save_id)
        if not saved_state:
            return False

        transition_time = self._seconds_to_transition_time(transition_time_seconds)

        if "light_states" in saved_state:
            light_states = saved_state["light_states"]
            success = False

            for light_id, original_state in light_states.items():
                restore_state = {
                    k: v
                    for k, v in original_state.items()
                    if k
                    in ["on", "bri", "hue", "sat", "xy", "ct", "effect", "colormode"]
                }

                restore_state["transitiontime"] = transition_time

                await self.set_light_state(light_id, restore_state)
                success = True

            return success

        if "group_state" in saved_state:
            group_state = saved_state["group_state"]
            restore_state = {
                k: v
                for k, v in group_state.items()
                if k in ["on", "bri", "hue", "sat", "xy", "ct", "effect", "colormode"]
            }

            restore_state["transitiontime"] = transition_time
            await self.set_state(restore_state)
            return True

        restore_state = {
            k: v
            for k, v in saved_state.items()
            if k in ["on", "bri", "hue", "sat", "xy", "ct", "effect", "colormode"]
        }

        restore_state["transitiontime"] = transition_time
        await self.set_state(restore_state)
        return True

    def get_saved_state(self, save_id: str) -> Optional[GroupState]:
        """
        Retrieve a saved state from the repository.
        """
        return self.state_repository.get_state(save_id)

    @property
    def saved_states(self) -> Dict[str, GroupState]:
        """
        Get all saved states for this group.
        """
        return self.state_repository.saved_states

    async def subtle_light_change(
        self,
        base_hue_shift: int = 1000,
        hue_variation: int = 500,
        sat_adjustment: int = 0,
        sat_variation: int = 10,
        transition_time_seconds: float = 1.0,
    ) -> str:
        """
        Creates subtle and varied color changes to individual lights in the group
        without affecting their brightness.
        """
        state_id = await self.save_state()

        transition_time = self._seconds_to_transition_time(transition_time_seconds)

        light_ids = await self.get_lights_in_group()

        for light_id in light_ids:
            light_state = await self.get_light_state(light_id)

            if not light_state.get("on", False):
                continue

            new_light_state = {"on": True}

            if "hue" in light_state:
                individual_hue_shift = base_hue_shift + random.randint(
                    -hue_variation, hue_variation
                )
                new_light_state["hue"] = (
                    light_state["hue"] + individual_hue_shift
                ) % 65536

            if "sat" in light_state and (sat_adjustment != 0 or sat_variation != 0):
                individual_sat_adjustment = sat_adjustment + random.randint(
                    -sat_variation, sat_variation
                )
                new_light_state["sat"] = max(
                    0, min(254, light_state["sat"] + individual_sat_adjustment)
                )

            if "colormode" in light_state:
                new_light_state["colormode"] = light_state["colormode"]

            new_light_state["transitiontime"] = transition_time

            await self.set_light_state(light_id, new_light_state)

        return state_id

    async def get_lights_in_group(self) -> List[str]:
        """
        Get a list of light IDs that belong to this group.
        """
        await self._refresh_group_info()
        if not self._group_info:
            raise RuntimeError(self.NOT_INITIALIZED_ERROR_MSG)

        return self._group_info.get("lights", [])

    async def get_light_state(self, light_id: str) -> Dict[str, Any]:
        """
        Get the current state of a specific light.
        """
        light_info = await self.bridge.get_request(f"lights/{light_id}")
        return light_info.get("state", {})

    async def set_light_state(
        self, light_id: str, state: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Set the state of a specific light.
        """
        return await self.bridge.put_request(f"lights/{light_id}/state", state)

    def _seconds_to_transition_time(self, seconds: float) -> int:
        """
        Convert seconds to Hue API transition time units (100ms units).
        """
        return max(1, round(seconds * 10))
