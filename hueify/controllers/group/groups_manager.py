from typing import Dict

from hueify import HueBridge

from hueify.controllers.group.group_controller_factory import GroupControllerFactory
from hueify.controllers.group.group_state_repository import GroupService
from hueify.controllers.group.group_controller import GroupController

from hueify.models.group_info import GroupInfo


class GroupsManager:
    """
    Manager for all Philips Hue light groups.

    This class provides methods to retrieve information about all available groups
    and get controllers for specific groups.
    """

    def __init__(self, bridge: HueBridge) -> None:
        """
        Initialize the GroupsManager with a Hue Bridge.
        """
        self.bridge = bridge
        self.group_service = GroupService(bridge)
        self.controller_factory = GroupControllerFactory(bridge)

    async def get_all_groups(self) -> Dict[str, GroupInfo]:
        """
        Retrieve all light groups from the Hue Bridge.
        """
        return await self.controller_factory.get_cached_groups()

    async def get_controller(self, group_identifier: str) -> GroupController:
        """
        Get a controller for the specified group.
        """
        return await self.controller_factory.get_controller(group_identifier)

    async def get_available_groups_formatted(self) -> str:
        """
        Get a formatted overview of all available groups.
        """
        return await self.controller_factory.get_available_groups_formatted()
