import asyncio

from hueify.sse.models import (
    ButtonEvent,
    GroupedLightEvent,
    LightEvent,
    MotionEvent,
)
from hueify.sse.monitor import EventMonitor


async def main():
    monitor = EventMonitor()

    def on_button_pressed(event: ButtonEvent):
        print("🎮 Button pressed!")
        print(f"   Button ID: {event.id}")
        print(f"   Event: {event.button.last_event.value}")
        print(f"   Updated: {event.button.button_report.updated}")

    def on_motion(event: MotionEvent):
        if event.motion.motion_valid:
            print("🚶 Motion detected!")
            print(f"   Sensor ID: {event.id}")
            print(f"   Motion: {event.motion.motion}")

    def on_light_changed(event: LightEvent):
        print("💡 Light changed:")
        print(f"   ID: {event.id}")

        if event.on:
            print(f"   On: {event.on.on}")
        if event.dimming:
            print(f"   Brightness: {event.dimming.brightness:.2f}%")
        if event.color:
            print(f"   Color XY: ({event.color.xy.x:.4f}, {event.color.xy.y:.4f})")

    def on_room_changed(event: GroupedLightEvent):
        print("🏠 Room light state changed:")
        print(f"   ID: {event.id}")
        print(f"   Type: {event.type}")

        if event.on:
            print(f"   On: {event.on.on}")
        if event.dimming:
            print(f"   Brightness: {event.dimming.brightness:.2f}%")

    # Register handlers
    monitor.on_button_press(on_button_pressed)
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
