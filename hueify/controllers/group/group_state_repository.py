from typing import Any, Dict, List, Optional
from hueify.bridge import HueBridge
from hueify.models.group_info import GroupInfo, GroupState


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
        """
        return self._saved_states.copy()

    def save_state(self, state_id: str, group_state: GroupState) -> None:
        """
        Save a group state with the specified ID.
        """
        self._saved_states[state_id] = group_state.copy()

    def get_state(self, state_id: str) -> Optional[GroupState]:
        """
        Retrieve a saved state by its ID.
        """
        return self._saved_states.get(state_id)

    def set_last_off_state(self, state_id: str) -> None:
        """
        Set the ID of the last saved state before turning off.
        """
        self._last_off_state_id = state_id

    def get_last_off_state(self) -> Optional[str]:
        """
        Get the ID of the last saved state before turning off.
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
        """
        self.bridge = bridge

    async def get_all_groups(self) -> Dict[str, GroupInfo]:
        """
        Retrieve all groups from the Hue Bridge.
        """
        return await self.bridge.get_request("groups")

    async def get_group(self, group_id: str) -> GroupInfo:
        """
        Retrieve information about a specific group.
        """
        return await self.bridge.get_request(f"groups/{group_id}")

    async def set_group_state(
        self, group_id: str, state: GroupState
    ) -> List[Dict[str, Any]]:
        """
        Set the state of a specific group with improved handling.
        """
        state_copy = state.copy()

        explicit_on_state = "on" in state_copy
        on_state = state_copy.pop("on", True) if explicit_on_state else True

        results = []

        if state_copy:
            results.append(
                await self.bridge.put_request(f"groups/{group_id}/action", state_copy)
            )

        if explicit_on_state:
            results.append(
                await self.bridge.put_request(
                    f"groups/{group_id}/action", {"on": on_state}
                )
            )

        return results

    async def get_group_id_by_name(self, group_name: str) -> Optional[str]:
        """Find and return the group ID corresponding to the given name."""

        groups = await self.get_all_groups()

        for group_id, group_data in groups.items():
            if group_data.get("name") == group_name:
                return group_id

        return None
