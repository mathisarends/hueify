"""Dropping to the raw CLIP v2 payloads when a command is not enough.

The commands cover on/off, brightness, color and color temperature. For
everything else - effects, gradients, signaling - build a LightUpdate and
send it yourself. It is the same request the commands produce internally.
"""

import asyncio

from hueify import Hueify, LightUpdate
from hueify.models import DimmingState, EffectsState, OnState, SignalingState

# adjust to names that exist in your setup
LIGHT_NAME = "Desk"
ROOM_NAME = "Office"


async def main() -> None:
    async with Hueify() as hue:
        light = await hue.lights.find_by_name(LIGHT_NAME)

        # the explicit form of hue.lights.turn_on(light.id, brightness=50)
        result = await hue.lights.update(
            light.id,
            LightUpdate(on=OnState(on=True), dimming=DimmingState(brightness=50)),
        )
        print("touched:", [item.rid for item in result.data])
        await asyncio.sleep(2)

        # effects have no command of their own; not every lamp supports them
        await hue.lights.update(
            light.id, LightUpdate(effects=EffectsState(effect="candle"))
        )
        await asyncio.sleep(5)
        await hue.lights.update(
            light.id, LightUpdate(effects=EffectsState(effect="no_effect"))
        )

        # signaling has no command of its own either; apply() sends the raw
        # LightUpdate straight to the room's grouped light
        office = await hue.rooms.find_by_name(ROOM_NAME)
        await hue.rooms.apply(
            office.id,
            LightUpdate(signaling=SignalingState(signal="on_off", duration=5000)),
        )

        # the grouped light also carries the aggregated state of the room
        grouped = await hue.rooms.grouped_light(office.id)
        print("room state:", grouped.model_dump(mode="json", exclude_none=True))


if __name__ == "__main__":
    asyncio.run(main())
