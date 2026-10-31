"""Run with `uv run python benchmarks/clip_v2.py`; no bridge is contacted."""

import asyncio
import gc
import platform
import tracemalloc
from collections.abc import Awaitable, Callable
from statistics import median
from time import perf_counter
from uuid import UUID

import httpx
from pydantic import TypeAdapter

from hueify.credentials import HueBridgeCredentials
from hueify.http import HttpClient
from hueify.models import HueApiResponse, Light, LightEvent, LightUpdate
from hueify.resources import LightNamespace, RawNamespace, ResourceRegistry
from hueify.sse import EventBus

RESOURCE_ID = UUID("00000000-0000-0000-0000-000000000001")
SAMPLES = 5


class MemoryTransport(httpx.AsyncBaseTransport):
    def __init__(self, read: httpx.Response, write: httpx.Response) -> None:
        self.read = read
        self.write = write

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        response = self.read if request.method == "GET" else self.write
        return httpx.Response(200, content=response.content)


async def measure(
    label: str, operation: Callable[[], Awaitable[object]], iterations: int
) -> None:
    for _ in range(10):
        await operation()
    samples = []
    for _ in range(SAMPLES):
        gc.collect()
        started = perf_counter()
        for _ in range(iterations):
            await operation()
        samples.append((perf_counter() - started) / iterations * 1_000_000)
    print(f"{label}: {median(samples):.2f} us/op")


def measure_peak_memory(label: str, operation: Callable[[], object]) -> None:
    peaks = []
    for _ in range(SAMPLES):
        gc.collect()
        tracemalloc.start()
        result = operation()
        peaks.append(tracemalloc.get_traced_memory()[1] / 1024)
        tracemalloc.stop()
        del result
    print(f"{label}: {median(peaks):.1f} KiB peak Python allocations")


async def main() -> None:
    print(f"Python {platform.python_version()}, {platform.system()}, {SAMPLES} samples")
    read = httpx.Response(
        200,
        json={
            "data": [
                {
                    "id": str(RESOURCE_ID),
                    "type": "light",
                    "owner": {"rid": str(RESOURCE_ID), "rtype": "device"},
                    "metadata": {"name": f"Light {index}"},
                    "on": {"on": True},
                    "dimming": {"brightness": 50},
                    "color": {"xy": {"x": 0.3, "y": 0.4}},
                    "future_field": {"preserved": True},
                }
                for index in range(200)
            ],
            "errors": [],
        },
    )
    write = httpx.Response(
        200, json={"data": [{"rid": str(RESOURCE_ID), "rtype": "light"}], "errors": []}
    )
    credentials = HueBridgeCredentials(HUE_BRIDGE_IP="192.0.2.1", HUE_APP_KEY="a" * 40)
    async with HttpClient(credentials) as client:
        await client.close()
        client._client = httpx.AsyncClient(transport=MemoryTransport(read, write))
        adapter = TypeAdapter(HueApiResponse[Light])
        update = LightUpdate(on={"on": True})
        namespace = LightNamespace(client)
        bus = EventBus()
        event = LightEvent(id=RESOURCE_ID)

        await measure(
            "GET 200 lights (in-memory HTTP)", lambda: client.get("light", adapter), 300
        )
        await measure(
            "PUT response (in-memory HTTP)",
            lambda: client.put("light/id", update),
            2000,
        )
        await measure(
            "Exact name lookup (in-memory HTTP)",
            lambda: namespace.find_by_name("Light 100"),
            300,
        )
        await measure("Event without subscribers", lambda: bus.dispatch(event), 20000)

        async def registry() -> ResourceRegistry:
            return ResourceRegistry(client, [namespace])

        async def raw() -> RawNamespace:
            return RawNamespace("light", client)

        await measure("Resource registry construction", registry, 2000)
        await measure("Raw namespace construction", raw, 10000)
        measure_peak_memory(
            "200 lights via json() + validate_python()",
            lambda: adapter.validate_python(read.json()),
        )
        measure_peak_memory(
            "200 lights via validate_json()",
            lambda: adapter.validate_json(read.content),
        )


if __name__ == "__main__":
    asyncio.run(main())
