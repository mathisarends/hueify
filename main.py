import asyncio
import time
from bridge import HueBridge
from controllers.group_controller import GroupController, GroupsManager


async def usage_example_1():
    """Beispiel für die Verwendung des LightController als Facade."""
    bridge = HueBridge.connect_by_ip()
    
    manager = GroupsManager(bridge=bridge)

    lamp_controller = await manager.get_controller("Ikea Leuchte")
    
    room_controller = await manager.get_controller("Zimmer 1")
    
    await lamp_controller.turn_off()
    
    time.sleep(5)
    
    await lamp_controller.turn_on()
    

if __name__ == "__main__":
    # Wählen Sie eines der Beispiele aus
    asyncio.run(usage_example_1())
    # Oder: asyncio.run(usage_example_2())