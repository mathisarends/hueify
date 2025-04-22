import asyncio
from hueify import HueBridge, GroupsManager

async def subtle_light_demo():
    """Demonstration einer subtilen Farbänderung ohne Helligkeitsänderung."""
    try:
        print("🔌 Verbinde mit Hue Bridge...")
        bridge = HueBridge.connect_by_ip()

        manager = GroupsManager(bridge=bridge)

        room_controller = await manager.get_controller(group_identifier="Zimmer 1")
        
        # Zeige aktuellen Zustand
        print(f"📊 Ausgangszustand der Gruppe: {room_controller.state}")
        
        # Zeige Anzahl der Lichter in der Gruppe
        light_ids = await room_controller.get_lights_in_group()
        print(f"💡 Anzahl der Lichter in der Gruppe: {len(light_ids)}")
        
        # Individuelle subtile Farbänderung
        print("\n🔄 Führe individuelle subtile Farbänderungen durch...")
        original_state_id = await room_controller.subtle_individual_light_changes(
            base_hue_shift=5000,     # merkliche, aber sanfte Farbverschiebung
            hue_variation=2000,      # sorgt für etwas Unterschied zwischen den Lichtern
            sat_adjustment=20,       # leicht intensivere Farbe
            sat_variation=10,        # kleinere Variation der Sättigung
            transition_time=25       # sanfter Übergang über 2,5 Sekunden
        )
        print(f"💾 Original-Zustand gespeichert mit ID: {original_state_id}")
        
        # Zeige einige individuelle Lichtzustände
        await asyncio.sleep(3)  # Warte, bis Änderungen angewendet wurden
        print("\n📊 Beispiel für individuelle Lichtzustände:")
        for i, light_id in enumerate(light_ids[:3]):  # Zeige nur die ersten 3, falls viele existieren
            light_state = await room_controller.get_light_state(light_id)
            print(f"  Licht {light_id}: Farbwerte - Hue: {light_state.get('hue')}, Sat: {light_state.get('sat')}")
        
        print("\n⌨️ Drücke ENTER, um zum Originalzustand zurückzukehren...")
        await asyncio.get_event_loop().run_in_executor(None, input)
        
        print("🔙 Kehre zum Originalzustand zurück (mit individuellen Lichtwerten)...")
        await room_controller.restore_individual_light_states(original_state_id, transition_time=20)
        
        await asyncio.sleep(3)
        print(f"📊 Wiederhergestellter Gruppenszustand: {room_controller.state}")
        
    except ValueError as e:
        print(f"❌ Fehler: {e}")


if __name__ == "__main__":
    asyncio.run(subtle_light_demo())