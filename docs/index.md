# Hueify

**Async Python client for the Philips Hue API with real-time event streaming.**

Hueify wraps the Hue Bridge local REST API and SSE event stream behind clean,
high-level namespaces. State is kept in in-memory caches that are populated on
connect and kept live via server-sent events.

## Installation

```bash
pip install hueify
```

Optional extras:

```bash
pip install "hueify[mcp]"   # MCP server support
pip install "hueify[cli]"   # CLI support
```

## Quick start

```python
import asyncio
from hueify import Hueify

async def main() -> None:
    async with Hueify() as hue:
        await hue.lights.turn_on("Desk")
        await hue.rooms.activate_scene("Living Room", "Relax")

asyncio.run(main())
```

Credentials are read from the `HUE_BRIDGE_IP` and `HUE_APP_KEY` environment
variables, or passed directly:

```python
async with Hueify(bridge_ip="192.168.1.10", app_key="my-app-key") as hue:
    ...
```

## Namespaces at a glance

| Namespace | Access | Description |
|-----------|--------|-------------|
| `hue.lights` | [`LightNamespace`][hueify.light.LightNamespace] | Individual bulb control |
| `hue.rooms` | [`RoomNamespace`][hueify.grouped_lights.RoomNamespace] | Room-level grouped-light & scenes |
| `hue.zones` | [`ZoneNamespace`][hueify.grouped_lights.ZoneNamespace] | Zone-level grouped-light & scenes |
