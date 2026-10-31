"""Read sensors and device batteries, then listen to typed motion events."""

import asyncio

from hueify import Hueify
from hueify.models import MotionEvent, ResourceType


async def main() -> None:
    async with Hueify() as hue:
        for device in (await hue.devices.list()).data:
            print("device:", device.id, device.name)
        for power in (await hue.device_power.list()).data:
            if power.power_state:
                print("battery:", power.owner, power.power_state.battery_level)
        for temperature in (await hue.temperatures.list()).data:
            print("temperature:", temperature.id, temperature.celsius)
        for level in (await hue.light_levels.list()).data:
            print("light level:", level.id, level.lux)

        @hue.on(ResourceType.MOTION)
        async def on_motion(event: MotionEvent) -> None:
            print("motion:", event.id, event.detected)

        await hue.start_stream(timeout=5)
        await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
