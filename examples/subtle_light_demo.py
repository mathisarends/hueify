import asyncio
from hueify import HueBridge, GroupsManager


async def subtle_light_demo():
    """Demonstration of a subtle color change without brightness adjustment."""
    try:
        print("🔌 Connecting to Hue Bridge...")
        bridge = HueBridge.connect_by_ip()

        manager = GroupsManager(bridge=bridge)

        room_controller = await manager.get_controller(group_identifier="Zimmer 1")

        print(f"📊 Initial state of the group: {room_controller.state}")

        light_ids = await room_controller.get_lights_in_group()
        print(f"💡 Number of lights in the group: {len(light_ids)}")

        print("\n🔄 Performing individual subtle color changes...")
        original_state_id = await room_controller.subtle_light_change(
            base_hue_shift=5000,
            hue_variation=2000,
            sat_adjustment=20,
            sat_variation=10,
            transition_time_seconds=0.5,
        )
        print(f"💾 Original state saved with ID: {original_state_id}")

        await asyncio.sleep(3)

        print("\n⌨️ Press ENTER to return to the original state...")
        await asyncio.get_event_loop().run_in_executor(None, input)

        print("🔙 Returning to original state (with individual light values)...")
        await room_controller.restore_state(
            original_state_id, transition_time_seconds=0.5
        )

        await asyncio.sleep(3)

    except ValueError as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(subtle_light_demo())
