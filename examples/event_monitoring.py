# examples/event_monitoring.py
import asyncio

from hueify.sse.models import ResourceData
from hueify.sse.monitor import EventMonitor


async def main():
    monitor = EventMonitor()

    # Handler für Fernbedienungs-Events
    def on_button_pressed(resource: ResourceData):
        if not resource.button:
            return

        print("🎮 Button pressed!")
        print(f"   Button ID: {resource.id}")
        print(f"   Event: {resource.button.last_event.value}")
        print(f"   Updated: {resource.button.button_report.updated}")

    # Handler für Bewegungssensor
    def on_motion(resource: ResourceData):
        if not resource.motion:
            return

        if resource.motion.motion_valid:
            print("🚶 Motion detected!")
            print(f"   Sensor ID: {resource.id}")
            print(f"   Motion: {resource.motion.motion}")

    # Handler für Licht-Updates
    def on_light_changed(resource: ResourceData):
        print("💡 Light changed:")
        print(f"   ID: {resource.id}")

        if resource.on:
            print(f"   On: {resource.on.on}")
        if resource.dimming:
            print(f"   Brightness: {resource.dimming.brightness:.2f}%")
        if resource.color:
            print(
                f"   Color XY: ({resource.color.xy.x:.4f}, {resource.color.xy.y:.4f})"
            )

    # Handler für Raum-Licht-Updates
    def on_room_changed(resource: ResourceData):
        print("🏠 Room light state changed:")
        print(f"   ID: {resource.id}")
        print(f"   Type: {resource.type}")

        if resource.on:
            print(f"   On: {resource.on.on}")
        if resource.dimming:
            print(f"   Brightness: {resource.dimming.brightness:.2f}%")

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
