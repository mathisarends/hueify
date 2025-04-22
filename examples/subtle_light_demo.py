import asyncio
from hueify.bridge import HueBridge
from hueify.controllers.group_controller import GroupsManager


async def subtle_light_demo():
    """Demonstration einer subtilen Farbänderung ohne Helligkeitsänderung."""
    try:
        print("🔌 Verbinde mit Hue Bridge...")
        bridge = HueBridge.connect_by_ip()

        manager = GroupsManager(bridge=bridge)

        room_controller = await manager.get_controller(group_identifier="Zimmer 1")
        
        # Zeige aktuellen Zustand
        print(f"📊 Ausgangszustand: {room_controller.state}")
        
        # Subtile Farbänderung ohne Helligkeitsänderung
        print("\n🔄 Führe subtile Farbänderung durch (nur Farbe, gleiche Helligkeit)...")
        original_state_id = await room_controller.subtle_light_change(
            hue_shift=5000,
            sat_adjustment=10,
            transition_time=10
        )
        print(f"💾 Original-Zustand gespeichert mit ID: {original_state_id}")
        
        await asyncio.sleep(5)
        print(f"📊 Neuer Zustand: {room_controller.state}")
        print("💡 Helligkeit: {}%".format(await room_controller.get_current_brightness_percentage()))
        
        print("\n⌨️ Drücke ENTER, um zum Originalzustand zurückzukehren...")
        await asyncio.get_event_loop().run_in_executor(None, input)
        
        print("🔙 Kehre zum Originalzustand zurück...")
        await room_controller.restore_state(original_state_id, transition_time=10)
        
        await asyncio.sleep(5)
        print(f"📊 Wiederhergestellter Zustand: {room_controller.state}")
        
    except ValueError as e:
        print(f"❌ Fehler: {e}")


if __name__ == "__main__":
    asyncio.run(subtle_light_demo())