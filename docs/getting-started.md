# Getting Started

## Prerequisites

- Python 3.13+
- A Philips Hue Bridge on your local network
- A Hue application key (see [Hue developer docs](https://developers.meethue.com/develop/get-started-2/))

## Installation

```bash
pip install hueify
```

## Onboarding

If you don't have a bridge IP or app key yet, the `hueify setup` wizard handles everything for you. Requires the `cli` extra:

```bash
pip install hueify[cli]
hueify setup
```

The wizard auto-discovers the bridge on your network, prompts you to press the **link button**, and prints the two environment variables to export:

```
Hue Bridge Setup

Found bridge at 192.168.1.10

Press the link button on your Hue Bridge, then hit Enter.

Setup complete!

Add these to your environment:

  HUE_BRIDGE_IP=192.168.1.10
  HUE_APP_KEY=abc123...
```

---

## Configuration

Hueify reads credentials from environment variables by default:

```bash
export HUE_BRIDGE_IP=192.168.1.10
export HUE_APP_KEY=your-app-key
```

Or pass them directly when constructing [`Hueify`][hueify.Hueify]:

```python
hue = Hueify(bridge_ip="192.168.1.10", app_key="your-app-key")
```

## Connecting

Always use the async context manager so that `connect()` and `close()` are
called automatically:

```python
import asyncio
from hueify import Hueify

async def main() -> None:
    async with Hueify() as hue:
        print(hue.lights.names)   # ['Desk', 'Bedroom', ...]
        print(hue.rooms.names)    # ['Living Room', 'Kitchen', ...]

asyncio.run(main())
```

## Logging

Enable structured logging with:

```python
from hueify import configure_logging

configure_logging(level="DEBUG")
```
