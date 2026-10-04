"""Dropping to the raw CLIP v2 payloads when a command is not enough.

Use a LightUpdate when several features should change in one request, or use
hue.resources.of(...) to pass firmware-specific JSON through unchanged.
"""

import asyncio

from hueify import Hueify, LightUpdate
from hueify.models import (
    DimmingState,
    EffectAction,
    EffectsV2Update,
    OnState,
    SignalingUpdate,
)

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

        # The typed request underlying hue.lights.set_effect(); support varies.
        await hue.lights.update(
            light.id,
            LightUpdate(
                effects_v2=EffectsV2Update(action=EffectAction(effect="candle"))
            ),
        )
        await asyncio.sleep(5)
        await hue.lights.update(
            light.id,
            LightUpdate(
                effects_v2=EffectsV2Update(action=EffectAction(effect="no_effect"))
            ),
        )

        # apply() sends a LightUpdate to the room's grouped light.
        office = await hue.rooms.find_by_name(ROOM_NAME)
        await hue.rooms.apply(
            office.id,
            LightUpdate(signaling=SignalingUpdate(signal="on_off", duration=5000)),
        )

        # the grouped light also carries the aggregated state of the room
        grouped = await hue.rooms.grouped_light(office.id)
        print("room state:", grouped.model_dump(mode="json", exclude_none=True))


if __name__ == "__main__":
    asyncio.run(main())
