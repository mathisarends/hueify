# Hueify

[![PyPI](https://img.shields.io/pypi/v/hueify)](https://pypi.org/project/hueify/)
[![Python](https://img.shields.io/badge/python-3.13%2B-blue)](https://www.python.org/)

Hueify is a typed async client for the Philips Hue CLIP v2 API. Its public API is
ID-based, stateless and close to the JSON structures returned by a Hue Bridge.

```bash
pip install hueify
```

## Onboarding

The interactive setup discovers the bridge, registers an application key and
stores both values in the user configuration:

```python
from hueify.onboarding import setup

setup()
```

`Hueify()` reads this configuration automatically. `HUE_BRIDGE_IP` and
`HUE_APP_KEY`, or explicit constructor arguments, can override it.

## Resource API

Hueify exposes the four supported resource namespaces directly:

- `hue.lights`
- `hue.rooms`
- `hue.zones`
- `hue.scenes`

No resource inventory is loaded when the client is created or entered. Every
read addresses the bridge directly, either by resource type or stable Hue ID.

```python
import asyncio

from hueify import Hueify


LIGHT_ID = "ab859e4a-eb52-4984-90bb-9931386d9ef8"


async def main() -> None:
    async with Hueify() as hue:
        all_lights = await hue.lights.get_all()  # HueApiResponse[Light]
        light_response = await hue.lights.get(LIGHT_ID)
        light = light_response.data[0]

        print(light.id, light.metadata.name, light.on.on)


asyncio.run(main())
```

Responses preserve the native Hue envelope and are fully typed:

```python
HueApiResponse[Light](
    errors=[],
    data=[...],
)
```

All Hue models use Pydantic with `extra="allow"`. Known fields are statically
typed, while fields introduced by newer bridge firmware are retained. Convert a
response back to complete JSON with:

```python
payload = light_response.model_dump(mode="json")
```

## Updates

Updates use Pydantic request models and return
`HueApiResponse[ResourceIdentifier]` rather than an application-specific action
result:

```python
from hueify import Hueify, LightUpdate
from hueify.models import DimmingState, OnState


async with Hueify() as hue:
    result = await hue.lights.update(
        LIGHT_ID,
        LightUpdate(
            on=OnState(on=True),
            dimming=DimmingState(brightness=65),
        ),
    )
```

All namespaces support `get_all()` and `get(id)`. Lights additionally support
typed `update(id, LightUpdate)`. Rooms, zones and scenes expose their native
create, update and delete operations. Scenes also provide typed recall:

```python
result = await hue.scenes.recall(scene_id)
```

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

- Hue resource IDs are the only lookup keys.
- There are no light, grouped-light, room, zone or scene caches.
- Resource reads are snapshots; a later read gets current bridge state.
- Pydantic models mirror Hue resource JSON and retain additional fields.
- There are no agent-oriented messages, clamping results or `ActionResult`.
- The event connection is opt-in and independent of REST access.

## License

[MIT](LICENSE)
