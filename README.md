# Hueify

[![PyPI](https://img.shields.io/pypi/v/hueify)](https://pypi.org/project/hueify/)
[![Python](https://img.shields.io/badge/python-3.13%2B-blue)](https://www.python.org/)

Hueify is a typed async client for the Philips Hue CLIP v2 API. Lights, rooms and
zones share one command surface, and the raw JSON resources stay reachable
underneath it.

```bash
pip install hueify
```

- [Setup](#setup)
- [Quickstart](#quickstart)
- [Commands](#commands)
  - [Colors](#colors)
  - [Transitions](#transitions)
- [Finding resources](#finding-resources)
- [Reading state](#reading-state)
- [Rooms, zones and scenes](#rooms-zones-and-scenes)
- [Event stream](#event-stream)

## Setup

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
        await hue.lights.set_hex(desk.id, "#ff8800")
        await hue.lights.turn_off(desk.id, transition=2)

        office = await hue.rooms.find_by_name("Office")
        await hue.rooms.turn_on(office.id, brightness=70)


asyncio.run(main())
```

`Hueify` owns one HTTP client. Use it as an async context manager or call
`await hue.close()` yourself; entering it does not talk to the bridge yet.

## Commands

`hue.lights`, `hue.rooms` and `hue.zones` understand the same commands. A room or
zone is switched through its grouped light, so it takes one bridge call instead of
one per lamp - hueify resolves that service for you.

| Command | Effect |
| --- | --- |
| `turn_on(id, brightness=…, kelvin=…)` | Switch on, optionally in one shot |
| `turn_off(id)` | Switch off |
| `toggle(id)` | Read the current state and flip it |
| `is_on(id)` | `True` if the light or group is on |
| `set_brightness(id, 65)` | Absolute brightness in percent; `0` switches off |
| `brighten(id, by=10)` / `dim(id, by=10)` | Relative step, applied by the bridge |
| `set_hex(id, "#ff8800")` | Color from a hex string, `#rgb` or `#rrggbb` |
| `set_rgb(id, 0, 128, 255)` | Color from three 0-255 channels |
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

One command per color format, so the signature says which one it wants. Both
take `brightness` and `transition`, and both switch the light on:

```python
await hue.lights.set_hex(desk.id, "#ff8800")     # or "#f80"
await hue.lights.set_rgb(desk.id, 0, 128, 255)
```

`set_hex(id, "warm white")` fails rather than guessing.

Color temperatures are given in kelvin and clamped to the 2000-6500 K range Hue
lamps support. `hueify.color` exposes the conversions themselves - `to_xy`,
`hex_to_rgb`, `xy_to_hex`, `kelvin_to_mirek` - and `to_xy` is the lenient one:
it takes a hex string, a name from `NAMED_COLORS`, an RGB tuple or a `ColorXY`.
That is what you want for colors that arrive as strings, and for CIE xy, which
`set_state` passes through unchanged:

```python
from hueify.color import to_xy

await hue.lights.set_state(desk.id, on=True, color=to_xy(configured_color))
await hue.lights.set_state(desk.id, on=True, color=ColorXY(x=0.5, y=0.4))
```

### Transitions

Any command takes a `transition`, in seconds or as a `timedelta`. The bridge runs
the fade:

```python
from datetime import timedelta

await hue.lights.set_brightness(desk.id, 100, transition=timedelta(seconds=10))
await hue.rooms.turn_off(office.id, transition=3)
```

## Finding resources

IDs are the lookup keys, names are what you see in the Hue app. Every namespace
resolves both, and unwraps single resources for you:

```python
light = await hue.lights.find_by_name("Desk")       # ignores case and surrounding space
light = await hue.lights.find_by_name("desklamp")   # close enough also matches
light = await hue.lights.get_one(light.id)          # by ID, the resource itself
```

`find_by_name` takes an exact match first and otherwise falls back to the closest
name above a similarity cutoff. If nothing is close enough it raises
`ResourceNotFoundError` listing the names it did find, which is usually enough to
spot the typo.

The envelope-returning reads stay available for callers that want the errors
alongside the data:

```python
response = await hue.lights.list()   # HueApiResponse[Light]
response = await hue.lights.get(light.id)

print(response.errors, response.data)
```

## Reading state

Resources come back as Pydantic models mirroring the CLIP v2 JSON. State lives in
optional sub-models there, so lights and grouped lights carry flat accessors next
to the raw fields:

```python
light = await hue.lights.get_one(desk.id)

light.name          # metadata.name
light.is_on         # bool | None
light.brightness    # float | None, percent
light.mirek         # int | None
light.xy            # ColorXY | None
light.on.on         # the underlying field is still right there
```

All Hue models use Pydantic with `extra="allow"`. Known fields are statically
typed, while fields introduced by newer bridge firmware are retained. Convert a
response back to complete JSON with `response.model_dump(mode="json")`.

Reads are snapshots. Nothing is cached and nothing is polled in the background, so
a later read returns whatever the bridge reports then. To follow changes as they
happen, use the event stream.

## Rooms, zones and scenes

A room groups devices, a zone groups light services, and scenes belong to either.
Both namespaces resolve that hierarchy:

```python
office = await hue.rooms.find_by_name("Office")

for light in await hue.rooms.lights(office.id):
    print(light.name, light.is_on)

for scene in await hue.rooms.scenes(office.id):
    print(scene.name)

await hue.scenes.activate(scene.id, brightness=40, transition=2)
await hue.scenes.activate(scene.id, dynamic=True)
```

`hue.rooms.grouped_light(id)` returns the aggregated state of a group, and
`hue.rooms.apply(id, LightUpdate(...))` sends a raw update to it. Rooms, zones and
scenes also expose their native create, update and delete operations, and
`hue.scenes.recall(id, SceneRecallRequest(...))` remains available next to
`activate` for the full recall payload.

## Event stream

Entering `Hueify` does not connect to the SSE stream. Register handlers with the
`@hue.on(...)` decorator, then start the stream explicitly:

```python
import asyncio

from hueify import Hueify
from hueify.models import HueEvent, LightEvent, ResourceType


async with Hueify() as hue:
    @hue.on(ResourceType.LIGHT)
    async def on_light(event: LightEvent) -> None:
        print(event.id, event.is_on, event.brightness)

    @hue.on("*")
    async def on_any(event: HueEvent) -> None:
        print(event.type, event.id)

    await hue.start_stream()
    await asyncio.Event().wait()
```

Events arrive as `LightEvent`, `RoomEvent`, `ZoneEvent` and `SceneEvent` - the
matching update model plus an ID, so a `LightEvent` reads like a light, including
the flat accessors. Anything else arrives as the base `HueEvent`. A `"*"` handler
receives every event, in addition to the type-specific ones.

`hue.off(resource_type, handler)` removes a handler and `hue.stop_stream()` ends
the stream. Leaving the context manager closes a started stream along with the
HTTP client. Subscribing and starting live on the client; `hue.events` owns the
connection itself and reports its state.

### Reconnects

Bridges reboot, get new IPs and drop connections; the stream reconnects on its
own with an exponential, jittered backoff until you stop it. It gives up on one
thing only: an application key the bridge rejects, because retrying cannot fix
that. Configure the timing with `Hueify(reconnect=ReconnectPolicy(...))`.

What a reconnect cannot do is replay what happened while the connection was
down. The stream resumes with `Last-Event-ID`, so the bridge closes brief gaps
from its short buffer, but a longer outage loses events for good. If you keep a
local copy of bridge state, re-read it whenever the connection comes back:

```python
from hueify import ConnectionStatus

@hue.on_connection_change
async def on_connection(status: ConnectionStatus) -> None:
    if status.connected:
        await resync()
```

| Property | Meaning |
| --- | --- |
| `hue.events.running` | The stream is supervised - connected or reconnecting |
| `hue.events.connected` | The connection to the bridge is open right now |
| `hue.events.status` | `connected`, `since` and `last_event_at` in one snapshot |
| `hue.events.last_error` | The latest connection failure; cleared after recovery |

`hue.start_stream()` returns as soon as the stream is supervised, which is what
a long-running app wants. A script that needs to be listening before it changes
anything can pass `hue.start_stream(timeout=5)` instead: it waits for the first
connection and raises if the bridge does not answer - with the rejected key or
connection error as the cause, rather than a bare timeout. The stream keeps
reconnecting either way. To wait for a *re*connection later on, use
`await hue.events.wait_connected(timeout=5)`, which returns `False` on timeout.

Because the bridge stays silent while nothing changes, silence is not a health
signal - `read_timeout` (90s by default) only bounds how long a dead socket can
look alive before the stream reconnects.

## Examples

Runnable scripts for each use case live in [examples/](examples/).

## License

[MIT](LICENSE)
