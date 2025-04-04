import asyncio
import time
from hueify.bridge import HueBridge
from hueify.controllers.group_controller import GroupsManager

async def usage_example_1():
    """Beispiel für die Verwendung des LightController als Facade."""
    bridge = HueBridge.connect_by_ip()
    
    manager = GroupsManager(bridge=bridge)

    lamp_controller = await manager.get_controller("Ikea Leuchte")
    
    room_controller = await manager.get_controller("Zimmer 1")
    
    await lamp_controller.turn_off()
    
    time.sleep(5)
    
    await lamp_controller.turn_on()
    
    await room_controller.activate_scene("Majestätischer Morgen")
    
    time.sleep(5)
    
    await room_controller.increase_brightness_percentage(30)
    

if __name__ == "__main__":
    asyncio.run(usage_example_1())
