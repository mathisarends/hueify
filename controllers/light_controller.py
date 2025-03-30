from __future__ import annotations
from typing import Any, Dict, List, Literal, Optional, TypedDict
import asyncio
from bridge import HueBridge


class LightStateDict(TypedDict, total=False):
    """Type definition for the state of a light."""
    on: bool
    bri: int
    hue: int
    sat: int
    xy: List[float]
    ct: int  
    effect: Literal["none", "colorloop"]
    colormode: Literal["hs", "xy", "ct"]
    alert: Literal["none", "select", "lselect"]
    transitiontime: Optional[int]
    reachable: bool
    mode: str


class LightStateRepository:
    """Repository for storing and retrieving light states."""
    
    def __init__(self) -> None:
        self._saved_states: Dict[str, Dict[str, LightStateDict]] = {}
        self._last_off_state_id: Optional[str] = None
    
    @property
    def saved_states(self) -> Dict[str, Dict[str, LightStateDict]]:
        return self._saved_states.copy()
    
    def save_state(self, state_id: str, light_states: Dict[str, LightStateDict]) -> None:
        self._saved_states[state_id] = light_states.copy()
    
    def get_state(self, state_id: str) -> Optional[Dict[str, LightStateDict]]:
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


class LightService:
    """Service for interacting with bridge APIs to control lights."""
    
    def __init__(self, bridge: HueBridge) -> None:
        self.bridge = bridge
    
    async def get_all_lights(self) -> Dict[str, Any]:
        return await self.bridge.get_request("lights")
    
    async def set_light_state(self, light_id: str, state: LightStateDict) -> List[Any]:
        return await self.bridge.put_request(f"lights/{light_id}/state", state)
    
    async def get_light_state(self, light_id: str) -> LightStateDict:
        light_data = await self.bridge.get_request(f"lights/{light_id}")
        return light_data.get("state", {})


class LightSwitch:
    """Handles turning lights on and off with state persistence."""
    
    def __init__(self, light_service: LightService, state_repository: LightStateRepository) -> None:
        self.light_service = light_service
        self.state_repository = state_repository
    
    async def turn_all_on(self) -> None:
        """Turn on all lights, restoring previous state if available."""
        last_state_id = self.state_repository.get_last_off_state()
        saved_state = None
        
        if last_state_id:
            saved_state = self.state_repository.get_state(last_state_id)
        
        if saved_state:
            for light_id, state in saved_state.items():
                restore_state = self._get_restorable_state(state)
                await self.light_service.set_light_state(light_id, restore_state)
            
            self.state_repository.clear_last_off_state()
        else:
            # No saved state, just turn all lights on
            lights = await self.light_service.get_all_lights()
            for light_id in lights:
                await self.light_service.set_light_state(light_id, {"on": True})
    
    async def turn_all_off(self) -> bool:
        lights = await self.light_service.get_all_lights()
        light_ids = list(lights.keys())
        
        # Collect current states
        states: Dict[str, LightStateDict] = {}
        for light_id in light_ids:
            if light_id in lights:
                states[light_id] = lights[light_id]["state"]
        
        # Save the states
        state_id = f"lights_before_off_{asyncio.get_event_loop().time()}"
        self.state_repository.save_state(state_id, states)
        self.state_repository.set_last_off_state(state_id)
        
        # Turn off all lights
        for light_id in light_ids:
            await self.light_service.set_light_state(light_id, {"on": False})
            
        return True
    
    def _get_restorable_state(self, state: LightStateDict) -> LightStateDict:
        """Extract restorable properties from a light state."""
        return {
            k: v
            for k, v in state.items()
            if k in ["on", "bri", "hue", "sat", "xy", "ct", "effect", "colormode"]
        }


class LightController:
    """Facade for light control operations, providing a simplified interface."""
    
    def __init__(self, bridge: HueBridge) -> None:
        self.state_repository = LightStateRepository()
        self.light_service = LightService(bridge)
        self.light_switch = LightSwitch(self.light_service, self.state_repository)
    
    async def turn_lights_on(self) -> bool:
        return await self.light_switch.turn_all_on()
    
    async def turn_lights_off(self) -> bool:
        return await self.light_switch.turn_all_off()
    
    async def get_all_lights(self) -> Dict[str, Any]:
        return await self.light_service.get_all_lights()
    
    async def set_light_state(self, light_id: str, state: LightStateDict) -> List[Any]:
        return await self.light_service.set_light_state(light_id, state)
    
    @property
    def saved_states(self) -> Dict[str, Dict[str, LightStateDict]]:
        return self.state_repository.saved_states
    
    async def save_light_states(self, light_ids: List[str], save_id: Optional[str] = None) -> str:
        if save_id is None:
            save_id = f"save_{'_'.join(light_ids)}"
            
        lights = await self.light_service.get_all_lights()
        states: Dict[str, LightStateDict] = {}
        for light_id in light_ids:
            if light_id in lights:
                states[light_id] = lights[light_id]["state"]
                
        self.state_repository.save_state(save_id, states)
        return save_id
    
    async def restore_light_states(self, save_id: str) -> bool:
        saved_state = self.state_repository.get_state(save_id)
        if not saved_state:
            return False
            
        for light_id, state in saved_state.items():
            restore_state = {
                k: v
                for k, v in state.items()
                if k in ["on", "bri", "hue", "sat", "xy", "ct", "effect", "colormode"]
            }
            
            await self.light_service.set_light_state(light_id, restore_state)
            
        return True
        
    def clear_saved_state(self, save_id: str) -> bool:
        return self.state_repository.remove_state(save_id)
    
    def get_saved_state(self, save_id: str) -> Optional[Dict[str, LightStateDict]]:
        return self.state_repository.get_state(save_id)