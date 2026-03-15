import asyncio
import contextlib
import logging

from hueify import Hueify
from hueify.sse.views import GroupedLightEvent, LightEvent, SceneEvent

logging.basicConfig(level=logging.WARNING)


async def main() -> None:
    async with Hueify() as hue:

        @hue.on(LightEvent)
        async def on_light(event: LightEvent) -> None:
            print(f"[light] {event.id} → on={event.on}, brightness={event.dimming}")
            light = hue.lights.from_id(event.id)
            print("light", light)

        @hue.on(GroupedLightEvent)
        async def on_grouped_light(event: GroupedLightEvent) -> None:
            print(f"[grouped] {event.id} → on={event.on}, brightness={event.dimming}")

        @hue.on(SceneEvent)
        async def on_scene(event: SceneEvent) -> None:
            print(f"[scene] {event.id} → {event.status}")

        print("Listening for events — press Ctrl+C to stop.\n")
        await asyncio.Event().wait()


if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(main())
