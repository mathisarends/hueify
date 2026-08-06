import asyncio
import contextlib

from hueify import ConnectionStatus, Hueify
from hueify.models import LightEvent, ResourceType, SceneEvent


async def main() -> None:
    async with Hueify() as hue:

        @hue.on(ResourceType.LIGHT)
        async def on_light(event: LightEvent) -> None:
            print(f"[light] {event.id} -> on={event.on}, brightness={event.dimming}")

        @hue.on(ResourceType.SCENE)
        async def on_scene(event: SceneEvent) -> None:
            print(f"[scene] {event.id} -> {event.status}")

        @hue.events.on_connection_change
        async def on_connection(status: ConnectionStatus) -> None:
            # Events that happened while the stream was down are gone, so this
            # is the moment to re-read whatever state you keep locally.
            state = "connected" if status.connected else "disconnected"
            print(f"[stream] {state} since {status.since:%H:%M:%S}")

        await hue.events.start()
        print("Listening for events - press Ctrl+C to stop.")
        await asyncio.Event().wait()


if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(main())
