from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
from bridge import HueBridge


class SceneInfo:
    """Information about a scene."""
    
    def __init__(self, scene_id: str, data: Dict[str, Any]) -> None:
        self.id = scene_id
        self.name = data.get("name", "")
        self.group_id = data.get("group", "")
        self.type = data.get("type", "")
        self.lights = data.get("lights", [])
        self.owner = data.get("owner", "")
        self.recycle = data.get("recycle", False)
        self.locked = data.get("locked", False)
        self.appdata = data.get("appdata", {})
        self.picture = data.get("picture", "")
        self.image = data.get("image", "")
        self.lastupdated = data.get("lastupdated", "")
        self.version = data.get("version", 0)
        self._data = data
    
    def __str__(self) -> str:
        return f"Scene: {self.name} (ID: {self.id})"


class SceneService:
    """Service for interacting with bridge APIs to control scenes."""
    
    def __init__(self, bridge: HueBridge) -> None:
        self.bridge = bridge
    
    async def get_all_scenes(self) -> Dict[str, Dict[str, Any]]:
        """Get all scenes from the bridge."""
        return await self.bridge.get_request("scenes")
    
    async def get_scenes_for_group(self, group_id: str) -> Dict[str, Dict[str, Any]]:
        """Get all scenes associated with a specific group."""
        all_scenes = await self.get_all_scenes()
        return {
            scene_id: scene_data 
            for scene_id, scene_data in all_scenes.items()
            if scene_data.get("group") == group_id
        }
    
    async def activate_scene(self, group_id: str, scene_id: str) -> List[Dict[str, Any]]:
        """Activate a scene in a specific group."""
        return await self.bridge.put_request(
            f"groups/{group_id}/action", {"scene": scene_id}
        )
    
    async def find_scene_by_name(self, scene_name: str, group_id: Optional[str] = None) -> Optional[Tuple[str, str]]:
        scenes = await self.get_all_scenes()
        
        for scene_id, scene_data in scenes.items():
            if scene_data.get("name") == scene_name:
                scene_group_id = scene_data.get("group")
                if scene_group_id and (group_id is None or scene_group_id == group_id):
                    return scene_id, scene_group_id
                    
        return None


class GroupSceneController:
    """Controller for managing scenes for a specific group."""
    
    def __init__(self, bridge: HueBridge, group_id: str) -> None:
        self.bridge = bridge
        self.group_id = group_id
        self.scene_service = SceneService(bridge)
        self._scenes_cache: Dict[str, SceneInfo] = {}
    
    async def get_available_scenes(self) -> Dict[str, SceneInfo]:
        scenes_data = await self.scene_service.get_scenes_for_group(self.group_id)
        
        self._scenes_cache = {
            scene_id: SceneInfo(scene_id, scene_data)
            for scene_id, scene_data in scenes_data.items()
        }
        
        return self._scenes_cache.copy()
    
    async def get_scene_names(self) -> List[str]:
        scenes = await self.get_available_scenes()
        return [scene.name for scene in scenes.values()]
    
    async def get_active_scene(self) -> Optional[str]:
        group_info = await self.bridge.get_request(f"groups/{self.group_id}")
        return group_info.get("action", {}).get("scene")
    
    async def activate_scene(self, scene_id: str) -> List[Dict[str, Any]]:
        return await self.scene_service.activate_scene(self.group_id, scene_id)
    
    async def activate_scene_by_name(self, scene_name: str) -> List[Dict[str, Any]]:
        """Activate a scene by name in this group.
        """
        for scene_id, scene_info in self._scenes_cache.items():
            if scene_info.name == scene_name:
                return await self.activate_scene(scene_id)
        
        result = await self.scene_service.find_scene_by_name(scene_name, self.group_id)
        if result:
            scene_id, _ = result
            return await self.activate_scene(scene_id)
            
        await self.get_available_scenes()
        
        available_scenes = await self.get_scene_names()
        scenes_list = "\n".join([f"  - {name}" for name in available_scenes])
        
        raise ValueError(
            f"Scene '{scene_name}' not found for group {self.group_id}. "
            f"Available scenes:\n{scenes_list}"
        )
    
    async def get_scene_info(self, scene_id_or_name: str) -> Optional[SceneInfo]:
        """Get information about a scene by ID or name.
        """
        if not self._scenes_cache:
            await self.get_available_scenes()
            
        if scene_id_or_name in self._scenes_cache:
            return self._scenes_cache[scene_id_or_name]
            
        for scene_info in self._scenes_cache.values():
            if scene_info.name == scene_id_or_name:
                return scene_info
                
        return None