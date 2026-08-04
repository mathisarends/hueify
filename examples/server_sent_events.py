import asyncio
import contextlib

from hueify import Hueify
from hueify.models import LightEvent, ResourceType, SceneEvent


async def main() -> None:
    async with Hueify() as hue:

        @hue.on(ResourceType.LIGHT)
        async def on_light(event: LightEvent) -> None:
            print(f"[light] {event.id} -> on={event.on}, brightness={event.dimming}")

        @hue.on(ResourceType.SCENE)
        async def on_scene(event: SceneEvent) -> None:
            print(f"[scene] {event.id} -> {event.status}")

        await hue.events.connect()
        print("Listening for events - press Ctrl+C to stop.")
        await asyncio.Event().wait()


if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(main())
