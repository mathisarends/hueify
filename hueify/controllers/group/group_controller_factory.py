from typing import Dict, List, Optional
from hueify.bridge import HueBridge
from hueify.controllers.group.group_controller import GroupController
from hueify.controllers.group.group_state_repository import GroupService
from hueify.models.group_info import GroupInfo

from rapidfuzz import process


class GroupControllerFactory:
    """
    Factory for creating and managing GroupController instances.

    This class provides methods to create and retrieve group controllers,
    with caching to avoid creating duplicate controllers for the same group.
    """

    def __init__(self, bridge: HueBridge) -> None:
        """
        Initialize the GroupControllerFactory with a Hue Bridge.
        """
        self.bridge = bridge
        self.group_service = GroupService(bridge)
        self._controllers_cache: Dict[str, GroupController] = {}
        self._groups_cache: Optional[Dict[str, GroupInfo]] = None

    async def get_cached_groups(self) -> Dict[str, GroupInfo]:
        """
        Get the current cached groups, refreshing the cache if necessary.
        """
        if not self._groups_cache:
            await self._refresh_groups_cache()
        return self._groups_cache.copy()

    async def _resolve_group_identifier(self, identifier: str) -> Optional[str]:
        """
        Resolves the group ID from an identifier (name or ID).
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
