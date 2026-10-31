# Hueify

[![PyPI](https://img.shields.io/pypi/v/hueify)](https://pypi.org/project/hueify/)
[![Python](https://img.shields.io/badge/python-3.13%2B-blue)](https://www.python.org/)

Hueify is a typed async client for the Philips Hue CLIP v2 API. Lights, rooms and
zones share one command surface, and the raw JSON resources stay reachable
underneath it.

Device services, sensors, smart scenes, behavior instances, connectivity,
MotionAware resources and integrations are also exposed through namespaces.
See the [CLIP v2 coverage and migration guide](docs/clip-v2-coverage.md) for
every endpoint, its request model, and the limits of the public specification.

```bash
pip install hueify
```

- [Setup](#setup)
- [CLI](#cli)
- [Quickstart](#quickstart)
- [Commands](#commands)
  - [Colors](#colors)
  - [Transitions](#transitions)
- [Finding resources](#finding-resources)
- [Devices, sensors and other resources](#devices-sensors-and-other-resources)
- [Reading state](#reading-state)
- [Rooms, zones and scenes](#rooms-zones-and-scenes)
- [Event stream](#event-stream)
- [Entertainment streaming](#entertainment-streaming)

## Setup

A bridge IP and an application key are needed. `hueify setup` discovers the
bridge, waits for the link button and prints them:

```bash
$ hueify setup
...
Setup complete. Hueify reads these values:

  HUE_BRIDGE_IP=192.168.1.10
  HUE_APP_KEY=Xf3k…
  HUE_CLIENT_KEY=a1b2…
```

Put them into your environment or a `.env` file and `Hueify()` picks them up.
The client key is only needed for [entertainment streaming](#entertainment-streaming),
and the bridge hands it out while registering - never again afterwards.

The individual steps are available too, and return their result:

```python
from hueify.onboarding import discover_bridges, register_app_key, setup

bridges = await discover_bridges()
app = await register_app_key(bridges[0].internalipaddress)
app.app_key, app.client_key

credentials = setup()  # the interactive flow, as HueBridgeCredentials
```

Constructor arguments win over the environment:

```python
hue = Hueify(bridge_ip="192.168.1.10", app_key="…")
```

Without any of these, `Hueify()` raises `MissingCredentialsError` and names
what is missing.

## CLI

The Python library has no command-line dependency. Install the optional CLI
extra when you want the `hueify` command:

```bash
pip install "hueify[cli]"
```

The CLI follows a predictable command shape: resource type first, action
second, then a UUID or a resource name. Names use the same exact-then-fuzzy
resolution as the Python API.

```bash
hueify setup
hueify light list
hueify light on "Desk" --brightness 60 --transition 0.3
hueify room off Office
hueify zone color Garden "#ff8800"
hueify scene activate "Movie time" --dynamic
hueify scene activate Relax --room Office --no-fuzzy
hueify entertainment start TV
```

| Group | Commands |
| --- | --- |
| `light`, `room`, `zone` | `list`, `on`, `off`, `toggle`, `brightness`, `color`, `temperature`, `identify` |
| `scene` | `list`, `activate` |
| `entertainment` | `list`, `start`, `stop` |

Every command reads `HUE_BRIDGE_IP`, `HUE_APP_KEY`, and, where needed,
`HUE_CLIENT_KEY` from the environment or `.env`; keys are deliberately not CLI
flags. Results always go to stdout; errors go to stderr.

Three global output modes make the CLI useful both interactively and in
scripts:

```bash
hueify light list                 # human table
hueify --plain light list         # id<TAB>name<TAB>state
hueify light list --json | jq .   # compact id/name/state objects
```

The global output flags may appear before or after a subcommand. `--json` and
`--plain` are mutually exclusive. Use `--no-color` for plain CI logs. Exit codes
are `0` for success, `1` for Hueify failures, `2` for invalid usage or values,
`3` for missing or invalid credentials, and `4` for network failures.

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

Commands that set brightness, color, effects or gradients switch the target on.
`set_state` sends only its given fields; power-up configuration, relative steps,
signaling and commands that stop an effect do not switch the light on.

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

Names shared by several resources raise `AmbiguousResourceError` with the
candidate IDs. The same applies to tied fuzzy matches. Pass `fuzzy=False` to
`find_by_name` for exact names only, or use the global CLI flag `--no-fuzzy`.
Scene lookups accept `group_id=room.id` (or a zone ID); CLI activation accepts
`--room NAME_OR_UUID` or `--zone NAME_OR_UUID`.

The envelope-returning reads stay available for callers that want the errors
alongside the data:

```python
response = await hue.lights.list()   # HueApiResponse[Light]
response = await hue.lights.get(light.id)

print(response.errors, response.data)
```

## Devices, sensors and other resources

The same `list()`, `get(id)` and `get_one(id)` reads are available on every
resource namespace. Named resources also support `find_by_name()`; services
without a name are skipped. `hue.resources.list()` calls the CLIP resource root
and returns a mixed, typed inventory. References can be followed directly:

```python
inventory = await hue.resources.list()
light = await hue.lights.find_by_name("Desk")
device = await hue.resources.get(light.owner)

await hue.devices.rename(device.id, "Desk lamp")
await hue.devices.identify(device.id)

for sensor in (await hue.temperatures.list()).data:
    print(sensor.celsius)
for sensor in (await hue.light_levels.list()).data:
    print(sensor.lux)

motion = (await hue.motions.list()).data[0]
await hue.motions.disable(motion.id)
await hue.motions.set_sensitivity(motion.id, 1)
```

Use native request models for multi-field updates, for example
`hue.behavior_instances.update(id, BehaviorInstanceUpdate(enabled=False))`.
Built-in namespaces expose create and delete only where the pinned public
specification documents them. A resource unavailable on a particular bridge
returns its native HTTP error or Hue error envelope.

Lights also expose `set_effect()` / `stop_effect()` using `effects_v2`,
`set_gradient()`, `set_timed_effect()` / `stop_timed_effect()` and
`set_powerup_preset()`. All light-command namespaces support `signal()`,
`warmer()`, `cooler()`, `stop_color_temperature()` and `stop_dimming()`.
`set_powerup_preset()` configures restart behavior without changing the light's
current on/off state. Feature availability comes from the light's reported
capabilities.

```python
await hue.lights.set_effect(light.id, "candle", speed=0.4)
await hue.lights.stop_effect(light.id)
await hue.lights.set_powerup_preset(light.id, "last_on_state")
await hue.grouped_lights.signal(grouped_light_id, "on_off", duration=5)
```

For fields or operations absent from the public schema, an explicit raw
namespace accepts dictionaries, retaining even explicit JSON nulls:

```python
await hue.resources.of("light").update(light.id, {"future_setting": None})
```

Raw method availability makes no assertion about what the bridge supports.
See the [coverage guide](docs/clip-v2-coverage.md) for the full namespace table,
smart-scene creation, request migrations and outstanding reference checks.

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

For repeated commands, resolve the service once and address it directly:

```python
service_id = await hue.rooms.grouped_light_id(office.id)
await hue.grouped_lights.turn_on(service_id, brightness=70)
await hue.grouped_lights.set_hex(service_id, "#ff8800")
```

Each direct write takes one PUT. Group `toggle` resolves the service once, reads
its current state and sends one PUT. State is always read fresh; if a group is
deleted and recreated, resolve its service again.

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

Every modeled resource has a corresponding partial event, including
`MotionEvent`, `TemperatureEvent`, `ButtonEvent` and `SmartSceneEvent`. Fields
absent from a change remain optional; `LightEvent` also has the flat state
accessors. Unknown firmware resource types arrive as the base `HueEvent`, with
their fields retained. A `"*"` handler receives every event alongside the
type-specific handlers.

`event.type` identifies the resource, such as `light`. `event.operation` carries
the envelope's action (`add`, `update` or `delete`), and `event.creationtime` its
timestamp. Both are `None` when absent; future action names are kept as strings.
Deletion events may contain only the resource ID and type:

```python
@hue.on(ResourceType.LIGHT)
async def on_light(event: LightEvent) -> None:
    if event.operation == "delete":
        print("Removed light:", event.id)
```

Unknown resource type names are preserved as strings in `HueEvent`. Malformed
events are logged and skipped individually, so valid events in the same payload
still arrive.

Reception and handlers run in separate tasks with a bounded queue of 256 events.
Change its capacity with `Hueify(event_queue_size=512)` and inspect the waiting
count at `hue.events.pending_events`. Events are handled in arrival order; all
handlers for one event finish before the next event begins. When the queue fills,
reception waits for space and logs the backpressure, without dropping events.
The queue survives reconnects. Before connected callbacks run, previously queued
events and their handlers finish, so an older queued event cannot overwrite the
state refreshed by those callbacks. Stopping the stream cancels the active
handlers and discards pending events; cancellation cleanup is still awaited.

`hue.off(resource_type, handler)` removes a handler and `hue.stop_stream()` ends
the stream. Leaving the context manager closes a started stream along with the
HTTP client. Subscribing and starting live on the client; `hue.events` owns the
connection itself and reports its state.

Calling `await hue.stop_stream()` from an event or connection callback requests
shutdown and returns without waiting on that callback itself. Outside callbacks,
the same call waits for cleanup to finish. Active callbacks should return after
requesting shutdown and may be cancelled at their next await.

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
These waits report the open transport; they do not wait for queued handlers or
the recovery callbacks to finish. A queued handler can therefore wait for the
transport to reconnect. It must not wait for a recovery callback, since that
callback runs after the queued handlers.

Because the bridge stays silent while nothing changes, silence is not a health
signal - `read_timeout` (90s by default) only bounds how long a dead socket can
look alive before the stream reconnects.

## Entertainment streaming

The REST API is not built for light shows: every command is an HTTPS request the
bridge queues, and a beat that arrives 300 ms late is not a beat. An
entertainment area is the other path - the bridge accepts DTLS datagrams on UDP
port 2100 and pushes their colors to the lamps at about 25 Hz, acknowledging
nothing.

The DTLS handshake needs one dependency, so streaming is an optional install:

```bash
pip install "hueify[entertainment]"
```

Areas themselves are created in the Hue app, because they carry the room
geometry a user placed their lamps in. Finding and inspecting them works without
the extra:

```python
areas = await hue.entertainment.list()
area = await hue.entertainment.find_by_name("TV")

[(channel.channel_id, channel.position.x) for channel in area.channels]
await hue.entertainment.is_streaming(area.id)
```

Opening a stream takes the area over, and leaving it gives the area back:

```python
async with hue.entertainment.stream(area) as stream:
    stream.set_all("#ff8800")
    await asyncio.sleep(2)
    stream.set(channel_id=0, color="blue", brightness=0.4)
    await asyncio.sleep(2)
```

`set` and `set_all` do not send anything - they write into the next frame, which
a loop of its own sends on a fixed clock, 50 times a second by default. That
decoupling is the point: colors may arrive whenever they happen to be ready, and
the stream still produces an even flow of datagrams, without queueing, dropping
or drifting. When nothing new arrives it resends the last frame, which is also
what keeps the area alive - a few seconds of silence and the bridge stops
listening.

Writes are synchronous and are read between awaits, so a frame is never sent
half-updated, however many channels one write touches.

### Sources

Hueify owns the delivery, not the light show. Anything that paints frames -
an audio analyser, a screen grabber, a Spotify integration - is a *source*: an
object with a `render` method, or a plain function.

```python
from hueify.entertainment import Frame, Tick


class Pulse:
    def render(self, frame: Frame, tick: Tick) -> None:
        frame.set_all("#ffffff", brightness=abs(math.sin(tick.elapsed)))


async with hue.entertainment.stream(area) as stream:
    await stream.run(Pulse())
```

`run` hands every frame to the source on its deadline and returns when the
stream stops - raising whatever stopped it, including anything the source
raised, because a source that cannot paint has nothing left to send. `render`
runs on the sending clock, so it must not block or await; a source with its own
connection or audio device keeps a background task and lets `render` read the
state it maintains. Sources own their own lifetime:

```python
async with SpotifySource(...) as source, hue.entertainment.stream(area) as stream:
    await stream.run(source)
```

Both styles can be mixed - `set_all` still applies while a source is running,
until the source overwrites those channels again.

### What the bridge allows

| Limit | Detail |
| --- | --- |
| One streamer | Opening fails while another application owns the area, and a later takeover shows up on the event stream rather than on the socket |
| ~25 Hz to the lamps | Sending faster than `DEFAULT_RATE` (50) buys nothing; `MAX_RATE` is 60 |
| 20 channels | The protocol addresses at most `MAX_CHANNELS` per area |
| No REST while streaming | The lamps of a streaming area ignore light commands until the stream ends |

A stream that stops on its own - because the bridge dropped it, or a source
failed - leaves the reason in `stream.error`, and `await stream.wait_closed()`
raises it. `stream.stats` reports frames sent, late frames and the rate.
Calling `await stream.open()` again after a failure first releases the previous
session. A successful open resets the error and statistics for the new session;
closing preserves the last session's statistics and error for inspection.

Because a takeover is not visible on the UDP socket, an application that has to
notice it subscribes to the [event stream](#event-stream):

```python
@hue.on(ResourceType.ENTERTAINMENT_CONFIGURATION)
async def on_area(event: EntertainmentConfigurationEvent) -> None:
    if not event.is_streaming:
        print("The bridge stopped listening to us.")
```

## Examples

Runnable scripts for each use case live in [examples/](examples/).

## License

[MIT](LICENSE)
