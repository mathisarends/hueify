# Hueify

[![PyPI](https://img.shields.io/pypi/v/hueify)](https://pypi.org/project/hueify/)
[![Python](https://img.shields.io/badge/python-3.13%2B-blue)](https://www.python.org/)
[![Docs](https://img.shields.io/badge/docs-mathisarends.github.io-blue)](https://mathisarends.github.io/hueify/)

Hueify is an async-first Python library for Philips Hue. It lets you control lights, rooms, zones and scenes using the same names you see in the Hue app, with state kept fresh via serversent events. It also ships an MCP server for LLM tools.

```bash
pip install hueify
```

---

## Usage

All interaction goes through the `Hueify` async context manager. It connects to the bridge, populates the cache from the REST API, and subscribes to SSE events so state is always current without polling.

```python
import asyncio
from hueify import Hueify


async def main() -> None:
    async with Hueify() as hue:
        # lights, rooms, zones are namespaces on the hue object
        await hue.rooms.turn_on("Living Room")


asyncio.run(main())
```

Credentials are read from the environment by default (`HUE_BRIDGE_IP`, `HUE_APP_KEY`). You can also pass them explicitly:

```python
async with Hueify(bridge_ip="192.168.1.10", app_key="your-app-key") as hue:
    ...
```

---

## Lights

```python
async with Hueify() as hue:
    await hue.lights.turn_on("Desk lamp")
    await hue.lights.turn_off("Desk lamp")

    await hue.lights.set_brightness("Desk lamp", 75)
    await hue.lights.increase_brightness("Desk lamp", 10)
    await hue.lights.decrease_brightness("Desk lamp", 10)

    await hue.lights.set_color_temperature("Desk lamp", 30)

    brightness = hue.lights.get_brightness("Desk lamp")
    print("Brightness:", brightness)
```

---

## Rooms

```python
async with Hueify() as hue:
    print(hue.rooms.names)  # list of all room names

    await hue.rooms.turn_on("Living Room")
    await hue.rooms.set_brightness("Living Room", 40)
    await hue.rooms.increase_brightness("Living Room", 20)
    await hue.rooms.set_color_temperature("Living Room", 35)

    await hue.rooms.activate_scene("Living Room", "Relax")

    active = hue.rooms.get_active_scene("Living Room")
    print("Active scene:", active.name if active else None)

    scenes = hue.rooms.scene_names("Living Room")
    print("Available scenes:", scenes)
```

---

## Zones

Zones work identically to rooms:

```python
async with Hueify() as hue:
    print(hue.zones.names)

    await hue.zones.turn_on("Downstairs")
    await hue.zones.set_brightness("Downstairs", 60)
    await hue.zones.activate_scene("Downstairs", "Focus")
```

---

## Error handling

All not-found errors raise `ResourceNotFoundException` with the resource type, the lookup name, and a list of fuzzy-matched suggestions:

```python
from hueify import Hueify, ResourceNotFoundException

async with Hueify() as hue:
    try:
        await hue.rooms.turn_on("Livng Room")  # typo
    except ResourceNotFoundException as e:
        print(e)
        # room 'Livng Room' not found. Did you mean: 'Living Room'?
```

---

## Real-time events via Server-Sent Events

Hueify subscribes to the Hue Bridge's SSE stream inside `__aenter__`. State
changes made outside your script — via the Hue app, a physical switch, or
another client — are applied to the cache automatically. No polling required.

You can also react to changes directly by subscribing to typed event classes:

```python
from hueify.sse.views import LightEvent

async with Hueify() as hue:
    @hue.on(LightEvent)
    async def on_light(event: LightEvent) -> None:
        light = hue.lights.from_id(event.id)
        print(light)  # Light(name='Desk', id=..., on=True, brightness=75.0%)

    await asyncio.Event().wait()
```

Supported event types include `LightEvent`, `GroupedLightEvent`, `SceneEvent`,
`MotionEvent`, `ButtonEvent`, `TemperatureEvent`, and more — see the
[Events guide](docs/guide/events.md) for the full list.

---

## MCP server

Hueify includes a Model Context Protocol server that exposes lights, rooms, and zones to compatible LLM tools. Requires the `mcp` extra:

```bash
pip install hueify[mcp]
```

The server uses the same `Hueify` context manager internally. Integration with a specific MCP host is not covered here.

---

## License

[MIT](LICENSE)
