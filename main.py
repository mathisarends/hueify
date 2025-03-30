import asyncio
from bridge import HueBridge
from controllers.light_controller import LightController, LightService, LightStateRepository


async def usage_example_1():
    """Beispiel für die Verwendung des LightController als Facade."""
    bridge = await HueBridge.connect()
    
    # Einfache Nutzung über die Facade
    controller = LightController(bridge)
    
    # Lichter abrufen
    lights = await controller.get_all_lights()
    print(f"Found {len(lights)} lights")
    
    # Lichter ausschalten
    await controller.turn_lights_off()
    print("All lights turned off")
    
    await asyncio.sleep(2)
    
    # Lichter wieder einschalten
    await controller.turn_lights_on()
    print("All lights restored to previous state")

if __name__ == "__main__":
    # Wählen Sie eines der Beispiele aus
    asyncio.run(usage_example_1())
    # Oder: asyncio.run(usage_example_2())