from typing import Any
import httpx

from hueify.bridge import HueBridge
from hueify.utils.logging import LoggingMixin


class HueifyClient(LoggingMixin):
    def __init__(self, bridge: HueBridge) -> None:
        self.bridge = bridge

    async def get(self, endpoint: str) -> Any:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.bridge.base_url}/{endpoint}")
            return response.json()

    async def put(self, endpoint: str, data: dict) -> Any:
        async with httpx.AsyncClient() as client:
            response = await client.put(f"{self.bridge.base_url}/{endpoint}", json=data)
            return response.json()