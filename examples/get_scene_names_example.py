import asyncio
import time
from hueify import HueBridge, GroupsManager


async def usage_example_1():
    """Beispiel für die Verwendung des LightController als Facade."""
    try:
        bridge = HueBridge.connect_by_ip()

        manager = GroupsManager(bridge=bridge)

        room_controller = await manager.get_controller(group_identifier="Zimmer 1")

        test = await room_controller.scene_controller.get_scene_names()
        print("test,", test)

        time.sleep(5)

        await room_controller.decrease_brightness_percentage(25)

    except ValueError as e:
        print(f"Fehler: {e}")


if __name__ == "__main__":
    asyncio.run(usage_example_1())
