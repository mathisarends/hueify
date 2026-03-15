# Events

Hueify maintains a live SSE connection to the Hue Bridge. You can subscribe
to typed events via [`Hueify.on`][hueify.Hueify.on] and unsubscribe via
[`Hueify.off`][hueify.Hueify.off].

## Event types

All event models live in `hueify.sse.views`:

| Class                     | Fired when                                           |
| ------------------------- | ---------------------------------------------------- |
| `LightEvent`              | A light's state changes (on/off, brightness, colour) |
| `GroupedLightEvent`       | A grouped-light resource changes                     |
| `SceneEvent`              | A scene is activated or updated                      |
| `MotionEvent`             | A motion sensor triggers                             |
| `ButtonEvent`             | A Hue button is pressed                              |
| `RelativeRotaryEvent`     | A rotary dial is turned                              |
| `TemperatureEvent`        | Temperature sensor reading changes                   |
| `LightLevelEvent`         | Ambient light level changes                          |
| `DevicePowerEvent`        | Battery state changes                                |
| `ZigbeeConnectivityEvent` | Zigbee connectivity status changes                   |

## Subscribing — direct call

```python
from hueify.sse.views import LightEvent

async def on_light_change(event: LightEvent) -> None:
    print(f"Light {event.id} changed")

async with Hueify() as hue:
    hue.on(LightEvent, on_light_change)
    await asyncio.sleep(60)
```

## Subscribing — decorator

```python
async with Hueify() as hue:
    @hue.on(LightEvent)
    async def on_light_change(event: LightEvent) -> None:
        print(f"Light {event.id} changed")

    await asyncio.sleep(60)
```

## Unsubscribing

```python
hue.off(LightEvent, on_light_change)
```

## How the SSE connection works

Hueify opens a persistent Server-Sent Events connection to the Hue Bridge
inside `__aenter__`. Every state change triggered externally — via the Hue app,
a physical switch, or another client — is pushed to your script in real time and
applied to the internal cache automatically. No polling required.

The connection is managed entirely by the `Hueify` context manager. You only
interact with it through `hue.on` and `hue.off`.

```python
import asyncio
import contextlib
from hueify import Hueify
from hueify.sse.views import GroupedLightEvent, LightEvent, SceneEvent

async def main() -> None:
    async with Hueify() as hue:

        @hue.on(LightEvent)
        async def on_light(event: LightEvent) -> None:
            light = hue.lights.from_id(event.id)
            print(light)  # Light(name='Desk', id=..., on=True, brightness=75.0%)

        @hue.on(GroupedLightEvent)
        async def on_grouped_light(event: GroupedLightEvent) -> None:
            print(f"[grouped] {event.id} → on={event.on}, brightness={event.dimming}")

        @hue.on(SceneEvent)
        async def on_scene(event: SceneEvent) -> None:
            print(f"[scene] {event.id} → {event.status}")

        print("Listening for events — press Ctrl+C to stop.")
        await asyncio.Event().wait()

if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(main())
```
