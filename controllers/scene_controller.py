from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple, TypedDict, cast

from bridge import HueBridge


class SceneData(TypedDict):
    """Type definition for Hue scene data."""
    name: str
    type: str
    group: str
    lights: List[str]
    owner: str
    recycle: bool
    locked: bool
    appdata: Dict[str, Any]
    picture: str
    lastupdated: str
    version: int


class SceneResponse(TypedDict):
    """Type definition for scene activation response."""
    success: Dict[str, Any]


class SceneController:
    def __init__(self, bridge: HueBridge) -> None:
        """Initialize the scene controller with a bridge instance.
        
        Args:
            bridge: The configured HueBridge instance used for API requests
        """
        self.bridge = bridge

    async def get_all_scenes(self) -> Dict[str, SceneData]:
        """Retrieve all scenes from the Hue bridge.
        """
        response = await self.bridge.get_request("scenes")
        return cast(Dict[str, SceneData], response)

    async def get_scene_names(self) -> List[str]:
        """Get a list of all available scene names.
        """
        scenes = await self.get_all_scenes()
        return [
            scene_data.get("name", "")
            for scene_id, scene_data in scenes.items()
            if scene_data.get("name")
        ]

    async def get_active_scene(self, group_id: Optional[str] = None) -> Optional[str]:
        """Determine the currently active scene in a group.
        """
        if group_id is None:
            group_controller = GroupController(self.bridge)
            group_id = await group_controller.get_active_group()
            
            if group_id is None:
                return None

        group_info = await self.bridge.get_request(f"groups/{group_id}")
        
        return group_info.get("action", {}).get("scene")

    async def activate_scene(self, group_id: str, scene_id: str) -> List[SceneResponse]:
        """Activate a scene for a specific group.
        """
        response = await self.bridge.put_request(
            f"groups/{group_id}/action", {"scene": scene_id}
        )
        return cast(List[SceneResponse], response)

    async def find_scene_by_name(self, scene_name: str) -> Tuple[str, str]:
        """Find a scene by its name and return its ID and group ID.
        """
        scenes = await self.get_all_scenes()

        for scene_id, scene_data in scenes.items():
            if scene_data.get("name") == scene_name:
                group_id = scene_data.get("group")
                if group_id:
                    return scene_id, group_id

        raise ValueError(f"Scene with name '{scene_name}' not found")

    async def activate_scene_by_name(self, scene_name: str) -> List[SceneResponse]:
        """Activate a scene by its name.
        """
        scene_id, group_id = await self.find_scene_by_name(scene_name)
        return await self.activate_scene(group_id, scene_id)
    
    async def get_scene_info(self, scene_id: str) -> SceneData:
        """Get detailed information about a specific scene.
        """
        response = await self.bridge.get_request(f"scenes/{scene_id}")
        
        if "error" in response:
            raise ValueError(f"Scene with ID '{scene_id}' not found")
            
        return cast(SceneData, response)