# Hueify

[![PyPI](https://img.shields.io/pypi/v/hueify)](https://pypi.org/project/hueify/)
[![Python](https://img.shields.io/badge/python-3.13%2B-blue)](https://www.python.org/)

Hueify is a typed async client for the Philips Hue CLIP v2 API. Lights, rooms and
zones share one command surface, and the raw JSON resources stay reachable
underneath it.

```bash
pip install hueify
```

## Onboarding

A bridge IP and an application key are needed. `hueify setup` discovers the
bridge, waits for the link button and prints both:

```bash
$ hueify setup
...
Setup complete. Hueify reads these two values:

  HUE_BRIDGE_IP=192.168.1.10
  HUE_APP_KEY=Xf3k…
```

Put both into your environment or a `.env` file and `Hueify()` picks them up.
The individual steps are available too, and return their result:

```python
from hueify.onboarding import discover_bridges, register_app_key, setup

bridges = await discover_bridges()
app_key = await register_app_key(bridges[0].internalipaddress)

credentials = setup()  # the interactive flow, as HueBridgeCredentials
```

Constructor arguments win over the environment:

```python
hue = Hueify(bridge_ip="192.168.1.10", app_key="…")
```

Without any of these, `Hueify()` raises `MissingCredentialsError` and names
what is missing.

## Quickstart

```python
import asyncio

from hueify import Hueify


async def main() -> None:
    async with Hueify() as hue:
        desk = await hue.lights.find_by_name("Desk")

        await hue.lights.turn_on(desk.id, brightness=60)
        await hue.lights.set_color(desk.id, "#ff8800")
        await hue.lights.turn_off(desk.id, transition=2)

        office = await hue.rooms.find_by_name("Office")
        await hue.rooms.turn_on(office.id, brightness=70)


asyncio.run(main())
```

## Commands

`hue.lights`, `hue.rooms` and `hue.zones` understand the same commands. A room or
zone is switched through its grouped light, so it takes one bridge call instead of
one per lamp - hueify resolves that service for you.

| Command | Effect |
| --- | --- |
| `turn_on(id, brightness=…, color=…, kelvin=…)` | Switch on, optionally in one shot |
| `turn_off(id)` | Switch off |
| `toggle(id)` | Read the current state and flip it |
| `is_on(id)` | `True` if the light or group is on |
| `set_brightness(id, 65)` | Absolute brightness in percent; `0` switches off |
| `brighten(id, by=10)` / `dim(id, by=10)` | Relative step, applied by the bridge |
| `set_color(id, "#ff8800")` | Color from hex, a name, an RGB tuple or CIE xy |
| `set_color_temperature(id, 2700)` | White point in kelvin |
| `set_state(id, …)` | Send exactly the given fields and nothing else |
| `identify(id)` | Let the lamp breathe so you can tell which one it is |

Every `set_*` command switches the target on, because asking for a brightness or a
color implies it. `set_state` does not: it sends what it is given.

```python
await hue.lights.set_state(desk.id, brightness=30)          # dim without switching on
await hue.lights.set_state(desk.id, on=True, mirek=370)     # raw mirek instead of kelvin
```

Every command returns the native `HueApiResponse[ResourceIdentifier]` of the
bridge.

### Colors

`set_color` and `turn_on(color=…)` accept whatever is convenient:

```python
await hue.lights.set_color(desk.id, "#ff8800")        # hex, long or short
await hue.lights.set_color(desk.id, "warm white")     # named color
await hue.lights.set_color(desk.id, (0, 128, 255))    # RGB tuple
await hue.lights.set_color(desk.id, ColorXY(x=0.5, y=0.4))
```

Color temperatures are given in kelvin and clamped to the 2000-6500 K range Hue
lamps support. `hueify.color` exposes the conversions themselves - `to_xy`,
`xy_to_hex`, `kelvin_to_mirek` - for rendering current state back to something
readable.

### Transitions

Any command takes a `transition`, in seconds or as a `timedelta`. The bridge runs
the fade:

```python
from datetime import timedelta

await hue.lights.set_brightness(desk.id, 100, transition=timedelta(seconds=10))
await hue.rooms.turn_off(office.id, transition=3)
```

## Rooms, zones and scenes

A room groups devices, a zone groups light services, and scenes belong to either.
Both namespaces resolve that hierarchy:

```python
office = await hue.rooms.find_by_name("Office")

for light in await hue.rooms.lights(office.id):
    print(light.metadata.name, light.on.on)

for scene in await hue.rooms.scenes(office.id):
    print(scene.metadata.name)

await hue.scenes.activate(scene.id, brightness=40, transition=2)
await hue.scenes.activate(scene.id, dynamic=True)
```

`hue.rooms.grouped_light(id)` returns the aggregated state of a group, and
`hue.rooms.apply(id, LightUpdate(...))` sends a raw update to it.

## Finding resources

Every namespace resolves the name shown in the Hue app, and unwraps single
resources for you:

```python
light = await hue.lights.find_by_name("Desk")  # by name, raises ResourceNotFoundError
light = await hue.lights.get_one(light.id)  # by ID, the resource itself
```

The envelope-returning reads stay available for callers that want the errors
alongside the data:

```python
response = await hue.lights.list()   # HueApiResponse[Light]
response = await hue.lights.get(light.id)

print(response.errors, response.data)
```

All Hue models use Pydantic with `extra="allow"`. Known fields are statically
typed, while fields introduced by newer bridge firmware are retained. Convert a
response back to complete JSON with `response.model_dump(mode="json")`.

## Raw updates

The commands cover on/off, brightness, color and color temperature. For everything
else, build the request model and send it - it is the same call the commands make
internally:

```python
from hueify import LightUpdate
from hueify.models import EffectsState

await hue.lights.update(light.id, LightUpdate(effects=EffectsState(effect="candle")))
```

Rooms, zones and scenes expose their native create, update and delete operations,
and `hue.scenes.recall(id, SceneRecallRequest(...))` remains available next to
`activate`.

## Optional event stream

Entering `Hueify` does not connect to the SSE stream. Register handlers with the
re-exported `@hue.on(...)` decorator, then start the stream explicitly:

```python
import asyncio

from hueify import Hueify
from hueify.models import LightEvent, ResourceType


async with Hueify() as hue:
    @hue.on(ResourceType.LIGHT)
    async def on_light(event: LightEvent) -> None:
        print(event.id, event.on, event.dimming)

    await hue.events.connect()
    await asyncio.Event().wait()
```

`hue.off(resource_type, handler)` removes a handler. The context manager closes
an explicitly started stream and the HTTP client.

## Design

- Commands are convenience over the CLIP v2 payloads, never a second state model.
- Hue resource IDs are the lookup keys; names are resolved against the bridge.
- There are no light, grouped-light, room, zone or scene caches.
- Resource reads are snapshots; a later read gets current bridge state.
- Pydantic models mirror Hue resource JSON and retain additional fields.
- The event connection is opt-in and independent of REST access.

## Examples

Runnable scripts for each use case live in [examples/](examples/).

## License

[MIT](LICENSE)
