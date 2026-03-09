# Events

Hueify maintains a live SSE connection to the Hue Bridge. You can subscribe
to typed events via [`Hueify.on`][hueify.Hueify.on] and unsubscribe via
[`Hueify.off`][hueify.Hueify.off].

## Event types

All event models live in `hueify.sse.views`:

| Class | Fired when |
|-------|-----------|
| `LightEvent` | A light's state changes (on/off, brightness, colour) |
| `GroupedLightEvent` | A grouped-light resource changes |
| `SceneEvent` | A scene is activated or updated |
| `MotionEvent` | A motion sensor triggers |
| `ButtonEvent` | A Hue button is pressed |
| `RelativeRotaryEvent` | A rotary dial is turned |
| `TemperatureEvent` | Temperature sensor reading changes |
| `LightLevelEvent` | Ambient light level changes |
| `DevicePowerEvent` | Battery state changes |
| `ZigbeeConnectivityEvent` | Zigbee connectivity status changes |

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
