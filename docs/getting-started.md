# Getting Started

## Prerequisites

- Python 3.13+
- A Philips Hue Bridge on your local network
- A Hue application key (see [Hue developer docs](https://developers.meethue.com/develop/get-started-2/))

## Installation

```bash
pip install hueify
```

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
