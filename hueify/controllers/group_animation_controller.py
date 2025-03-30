from __future__ import annotations
import asyncio
import math
from typing import Any, Dict, List, Optional

from bridge import HueBridge

# TODO: Das hier muss sinnvoll integriert werden
class GroupAnimationController:
    """Controller for managing animations on a Philips Hue light group."""
    
    def __init__(self, bridge: HueBridge, group_id: str) -> None:
        """Initialize the GroupAnimationController with a Hue Bridge and group ID."""
        self.bridge = bridge
        self.group_id = group_id
        self.running_animation = None
        self.should_stop = False
    
    def stop_animation(self) -> None:
        """Stop any running animation."""
        self.should_stop = True
        if self.running_animation and not self.running_animation.done():
            self.running_animation.cancel()
        self.running_animation = None
    
    async def _get_scene_light_states(self, scene_name: str) -> Dict[str, Dict[str, Any]]:
        """
        Get the target light states from a scene.
        """
        scenes = await self.bridge.get_request("scenes")
        scene_id = None
        
        for sid, scene_data in scenes.items():
            if scene_data.get("name") == scene_name and scene_data.get("group") == self.group_id:
                scene_id = sid
                break
        
        if not scene_id:
            raise ValueError(f"Scene '{scene_name}' not found for group {self.group_id}")
        
        scene_details = await self.bridge.get_request(f"scenes/{scene_id}")
        
        if "lightstates" in scene_details:
            return scene_details["lightstates"]
        
        return {}
    
    async def scene_based_sunrise(
        self,
        scene_name: str,
        duration_seconds: int = 540,
        start_brightness_percent: float = 0.01,
        restore_original: bool = False
    ) -> None:
        """
        Start a sunrise animation based on a scene.
        
        The lights will start with the color configuration from the scene but at a very
        low brightness, which will then increase to the brightness defined in the scene
        over the specified duration.
        """
        self.stop_animation()
        self.should_stop = False
        
        try:
            target_states = await self._get_scene_light_states(scene_name)
            target_light_ids = list(target_states.keys())
            
            print(f"Scene '{scene_name}' found with {len(target_light_ids)} lights")
            
            save_id = None
            if restore_original:
                save_id = f"sunrise_{self.group_id}_{asyncio.get_event_loop().time()}"
                
                # Get the current state of each light
                for light_id in target_light_ids:
                    light_state = await self.bridge.get_request(f"lights/{light_id}/state")
                    # We would save these states somewhere, but we'd need a repository
                    # For simplicity, we'll just print that we would save them
                    print(f"Would save state for light {light_id}: {light_state}")
            
            # Start the sunrise animation
            self.running_animation = asyncio.create_task(
                self._run_scene_based_sunrise(
                    target_light_ids,
                    target_states,
                    duration_seconds,
                    start_brightness_percent,
                    save_id
                )
            )
            
            return self.running_animation
            
        except Exception as e:
            print(f"Error starting scene-based sunrise: {e}")
            raise
    
    async def _run_scene_based_sunrise(
        self,
        light_ids: List[str],
        target_states: Dict[str, Dict[str, Any]],
        duration: int,
        start_brightness_percent: float,
        save_id: Optional[str]
    ) -> None:
        """
        Run the scene-based sunrise animation.
        
        Args:
            light_ids: List of light IDs to animate
            target_states: Target states for each light
            duration: Duration in seconds
            start_brightness_percent: Initial brightness as a percentage of target brightness
            save_id: ID of the saved state to restore after the animation
        """
        try:
            print(f"Starting scene-based sunrise for {len(light_ids)} lights over {duration} seconds...")
            
            # Initial state: turn lights on with scene color but minimal brightness
            for light_id in light_ids:
                if light_id in target_states:
                    target_state = target_states[light_id]
                    
                    # Determine initial brightness based on target brightness
                    target_brightness = target_state.get("bri", 254)
                    initial_brightness = max(1, int(target_brightness * start_brightness_percent))
                    
                    # Create a copy of the target state with reduced brightness
                    initial_state = target_state.copy()
                    initial_state["bri"] = initial_brightness
                    
                    # Apply the initial state
                    await self.bridge.put_request(f"lights/{light_id}/state", initial_state)
            
            # Short pause to ensure lights are on
            await asyncio.sleep(0.5)
            
            # Number of steps based on duration
            steps = min(180, max(30, duration // 3))
            step_duration = duration / steps
            
            for step in range(1, steps + 1):
                if self.should_stop:
                    break
                
                # Exponential progress for a more natural sunrise
                progress = math.pow(step / steps, 2)  # Quadratic function for exponential growth
                
                # Update brightness of each light
                for light_id in light_ids:
                    if light_id in target_states:
                        target_state = target_states[light_id]
                        target_brightness = target_state.get("bri", 254)
                        initial_brightness = max(1, int(target_brightness * start_brightness_percent))
                        
                        # Calculate current brightness
                        current_brightness = int(
                            initial_brightness + (target_brightness - initial_brightness) * progress
                        )
                        current_brightness = max(1, min(254, current_brightness))
                        
                        # Set only the brightness, keep all other values
                        await self.bridge.put_request(
                            f"lights/{light_id}/state",
                            {
                                "bri": current_brightness,
                                "transitiontime": int(step_duration * 10),  # In 0.1s units
                            },
                        )
                
                # Wait until next step
                await asyncio.sleep(step_duration)
            
            print("Sunrise completed!")
            
            # Restore original state if needed
            if save_id and not self.should_stop:
                # This would restore the saved states, but we'd need a repository
                # For simplicity, we'll just print that we would restore them
                print(f"Would restore saved states with ID '{save_id}'")
                
        except asyncio.CancelledError:
            print("Sunrise was cancelled.")
        except Exception as e:
            print(f"Error in sunrise: {e}")
            
            # Try to restore original state in case of error
            if save_id:
                try:
                    print(f"Would restore saved states with ID '{save_id}' after error")
                except Exception as restore_error:
                    print(f"Error restoring state: {restore_error}")