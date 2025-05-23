from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from rapidfuzz import process

from hueify.bridge import HueBridge


@dataclass
class SceneInfo:
    """
    Information about a Philips Hue scene.

    This dataclass represents a scene from the Philips Hue system, containing
    all the relevant properties and metadata about the scene.

    Attributes:
        id: Unique identifier of the scene
        name: Name of the scene
        group_id: ID of the group this scene belongs to
        type: Type of scene (e.g., 'LightScene', 'GroupScene')
        lights: List of light IDs included in this scene
        owner: Username of the scene owner
        recycle: Whether the scene can be automatically deleted
        locked: Whether the scene is locked against modifications
        appdata: Application-specific data for the scene
        picture: Picture identifier for the scene
        image: Image data or identifier for the scene
        lastupdated: Timestamp of when the scene was last updated
        version: Version number of the scene
        _data: Raw data from the bridge API
    """

    id: str
    name: str = ""
    group_id: str = ""
    type: str = ""
    lights: List[str] = field(default_factory=list)
    owner: str = ""
    recycle: bool = False
    locked: bool = False
    appdata: Dict[str, Any] = field(default_factory=dict)
    picture: str = ""
    image: str = ""
    lastupdated: str = ""
    version: int = 0
    _data: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        """
        String representation of the scene.

        Returns:
            A string with the scene name and ID
        """
        return f"Scene: {self.name} (ID: {self.id})"


class SceneService:
    """
    Service for interacting with bridge APIs to control scenes.

    This class provides methods to retrieve scene information from the Philips Hue
    bridge and activate scenes in specific groups.
    """

    def __init__(self, bridge: HueBridge) -> None:
        """
        Initialize the SceneService with a Hue Bridge.

        Args:
            bridge: The HueBridge instance to use for API requests
        """
        self.bridge = bridge

    async def get_scenes_for_group(self, group_id: str) -> Dict[str, Dict[str, Any]]:
        """
        Get all scenes associated with a specific group.

        Args:
            group_id: ID of the group to get scenes for

        Returns:
            A dictionary mapping scene IDs to their corresponding scene data,
            filtered to only include scenes associated with the specified group
        """
        all_scenes = await self.get_all_scenes()
        return {
            scene_id: scene_data
            for scene_id, scene_data in all_scenes.items()
            if scene_data.get("group") == group_id
        }

    async def find_scene_by_name(
        self, scene_name: str, group_id: Optional[str] = None
    ) -> Optional[Tuple[str, str]]:
        """
        Find a scene by name, optionally filtering by group.

        Args:
            scene_name: Name of the scene to find
            group_id: Optional group ID to filter by

        Returns:
            A tuple of (scene_id, group_id) if found, None otherwise
        """
        scenes = await self.get_all_scenes()

        for scene_id, scene_data in scenes.items():
            if scene_data.get("name") == scene_name:
                scene_group_id = scene_data.get("group")
                if scene_group_id and (group_id is None or scene_group_id == group_id):
                    return scene_id, scene_group_id

        return None

    async def activate_scene_by_id(
        self, group_id: str, scene_id: str
    ) -> List[Dict[str, Any]]:
        """
        Activate a scene in a specific group.

        Args:
            group_id: ID of the group to activate the scene in
            scene_id: ID of the scene to activate

        Returns:
            A list of responses from the Hue Bridge API
        """
        return await self.bridge.put_request(
            f"groups/{group_id}/action", {"scene": scene_id}
        )

    async def get_all_scenes(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all scenes from the bridge.

        Returns:
            A dictionary mapping scene IDs to their corresponding scene data
        """
        return await self.bridge.get_request("scenes")


class GroupSceneController:
    """
    Controller for managing scenes for a specific Philips Hue light group.

    This class provides methods to retrieve, activate, and manage scenes
    associated with a specific group.
    """

    def __init__(self, bridge: HueBridge, group_id: str) -> None:
        """
        Initialize the GroupSceneController with a Hue Bridge and group ID.

        Args:
            bridge: The HueBridge instance to use for API requests
            group_id: ID of the group to control scenes for
        """
        self.bridge = bridge
        self.group_id = group_id
        self.scene_service = SceneService(bridge)
        self._scenes_cache: Dict[str, SceneInfo] = {}


    async def get_available_scenes(self) -> Dict[str, SceneInfo]:
        """
        Get all available scenes for this group.

        This method refreshes the internal scenes cache and returns a copy.

        Returns:
            A dictionary mapping scene IDs to their corresponding SceneInfo objects
        """
        scenes_data = await self.scene_service.get_scenes_for_group(self.group_id)

        self._scenes_cache = {}
        for scene_id, scene_data in scenes_data.items():
            # Create a copy of scene_data to avoid modifying the original
            scene_data_copy = scene_data.copy()
            
            # Rename 'group' to 'group_id' to match SceneInfo field name
            if 'group' in scene_data_copy:
                scene_data_copy['group_id'] = scene_data_copy.pop('group')
            
            # Create SceneInfo instance
            self._scenes_cache[scene_id] = SceneInfo(scene_id, **scene_data_copy)

        return self._scenes_cache.copy()

    async def get_scene_names(self) -> List[str]:
        """
        Get a list of all scene names available for this group.

        Returns:
            A list of scene names
        """
        scenes = await self.get_available_scenes()
        return [scene.name for scene in scenes.values()]

    async def get_active_scene(self) -> Optional[str]:
        """
        Get the ID of the currently active scene in this group.

        Returns:
            The scene ID if an active scene is found, None otherwise
        """
        group_info = await self.bridge.get_request(f"groups/{self.group_id}")
        return group_info.get("action", {}).get("scene")

    async def activate_scene_by_name(self, scene_name: str) -> List[Dict[str, Any]]:
        """
        Activate a scene by name in this group, using fuzzy matching if necessary.
        """
        for scene_id, scene_info in self._scenes_cache.items():
            if scene_info.name == scene_name:
                return await self.scene_service.activate_scene_by_id(
                    group_id=self.group_id, scene_id=scene_id
                )

        result = await self.scene_service.find_scene_by_name(
            scene_name=scene_name, group_id=self.group_id
        )
        if result:
            scene_id, _ = result
            return await self.scene_service.activate_scene_by_id(
                group_id=self.group_id, scene_id=scene_id
            )

        await self.get_available_scenes()

        fuzzy_match = await self._find_closest_scene_name(scene_name)
        if fuzzy_match:
            return await self.activate_scene_by_name(fuzzy_match)

        available_scenes = await self.get_scene_names()
        scenes_list = "\n".join([f"  - {name}" for name in available_scenes])

        raise ValueError(
            f"Scene '{scene_name}' not found for group {self.group_id}. "
            f"Available scenes:\n{scenes_list}"
        )

    async def get_scene_info(self, scene_id_or_name: str) -> Optional[SceneInfo]:
        """
        Get information about a scene by ID or name.

        This method attempts to find the scene in the cache, refreshing it if necessary.

        Args:
            scene_id_or_name: ID or name of the scene to get information about

        Returns:
            The SceneInfo object if found, None otherwise
        """
        if not self._scenes_cache:
            await self.get_available_scenes()

        if scene_id_or_name in self._scenes_cache:
            return self._scenes_cache[scene_id_or_name]

        for scene_info in self._scenes_cache.values():
            if scene_info.name == scene_id_or_name:
                return scene_info

        return None

    async def _find_closest_scene_name(
        self, query: str, threshold: int = 80
    ) -> Optional[str]:
        """
        Find the most similar scene name using fuzzy matching.

        Args:
            query: The user-provided scene name.
            threshold: Minimum similarity score (0–100) to accept a match.

        Returns:
            The best-matching scene name if above threshold, otherwise None.
        """
        scene_names = await self.get_scene_names()

        result = process.extractOne(query, scene_names, score_cutoff=threshold)

        if result:
            best_match_name = result[0]
            return best_match_name

        return None
