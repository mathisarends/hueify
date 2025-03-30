import asyncio
from bridge import HueBridge
from controllers.group_controller import GroupController


async def usage_example_1():
    """Beispiel für die Verwendung des LightController als Facade."""
    bridge = HueBridge.connect_by_ip()
    
    controller = GroupController(bridge, group_name="Ikea Leuchte")

    controller
    
    # Lichter ausschalten
    await controller.turn_groups_off()
    print("All lights turned off")
    
    await asyncio.sleep(2)
    
    await controller.turn_groups_on()
    print("All lights restored to previous state")
    

if __name__ == "__main__":
    # Wählen Sie eines der Beispiele aus
    asyncio.run(usage_example_1())
    # Oder: asyncio.run(usage_example_2())