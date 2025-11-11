# examples/event_monitoring.py
import asyncio

from hueify.events.models import ResourceData
from hueify.events.monitor import EventMonitor


async def main():
    monitor = EventMonitor()

    # Handler für Fernbedienungs-Events
    def on_button_pressed(resource: ResourceData):
        # Access extra fields via model_extra or direct attribute access
        button_data = (
            resource.model_extra.get("button", {})
            if hasattr(resource, "model_extra")
            else {}
        )
        button_report = button_data.get("button_report", {}) if button_data else {}

        event_type = button_report.get("event") if button_report else "unknown"

        print("🎮 Button pressed!")
        print(f"   Button ID: {resource.id}")
        print(f"   Event: {event_type}")
        print(
            f"   Full data: {resource.model_extra if hasattr(resource, 'model_extra') else 'N/A'}"
        )

    # Handler für Bewegungssensor
    def on_motion(resource: ResourceData):
        motion_data = (
            resource.model_extra.get("motion", {})
            if hasattr(resource, "model_extra")
            else {}
        )
        is_valid = motion_data.get("motion_valid", False)

        if is_valid:
            print("🚶 Motion detected!")
            print(f"   Sensor ID: {resource.id}")
            print(f"   Motion data: {motion_data}")

    # Handler für Licht-Updates
    def on_light_changed(resource: ResourceData):
        print(resource)
        on_state = (
            resource.model_extra.get("on", {})
            if hasattr(resource, "model_extra")
            else {}
        )
        dimming = (
            resource.model_extra.get("dimming", {})
            if hasattr(resource, "model_extra")
            else {}
        )

        print("💡 Light changed:")
        print(f"   ID: {resource.id}")
        print(f"   On: {on_state.get('on', 'N/A')}")
        print(f"   Brightness: {dimming.get('brightness', 'N/A')}")

    # Handler für Raum-Licht-Updates
    def on_room_changed(resource: ResourceData):
        on_state = (
            resource.model_extra.get("on", {})
            if hasattr(resource, "model_extra")
            else {}
        )
        dimming = (
            resource.model_extra.get("dimming", {})
            if hasattr(resource, "model_extra")
            else {}
        )

        print("🏠 Room light state changed:")
        print(f"   ID: {resource.id}")
        print(f"   Type: {resource.type}")
        print(f"   On: {on_state.get('on', 'N/A')}")
        print(f"   Brightness: {dimming.get('brightness', 'N/A')}")

    # Register handlers
    monitor.on_button_event(on_button_pressed)
    monitor.on_motion_detected(on_motion)
    monitor.on_light_update(on_light_changed)
    monitor.on_grouped_light_update(on_room_changed)

    print("🎧 Listening for Hue events...")
    print("Press Ctrl+C to stop\n")

    try:
        await monitor.start()
    except KeyboardInterrupt:
        print("\n⏹️  Stopping...")
        monitor.stop()


if __name__ == "__main__":
    asyncio.run(main())
