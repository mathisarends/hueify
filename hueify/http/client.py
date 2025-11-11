from typing import Any
from pydantic import BaseModel
import httpx

from hueify.credentials import HueBridgeCredentials
from hueify.http.models import ApiResponse
from hueify.utils.logging import LoggingMixin


class HttpClient(LoggingMixin):
    def __init__(
        self, 
        credentials: HueBridgeCredentials | None = None,
        timeout: float = 10.0,
    ) -> None:
        self._credentials = credentials or HueBridgeCredentials()
        self._client = httpx.AsyncClient(timeout=timeout)

    @property
    def base_url(self) -> str:
        if not self._credentials.hue_bridge_ip or not self._credentials.hue_user_id:
            raise ValueError("Credentials not properly configured")
        return f"http://{self._credentials.hue_bridge_ip}/api/{self._credentials.hue_user_id}"

    async def get(self, endpoint: str) -> ApiResponse:
        response = await self._client.get(f"{self.base_url}/{endpoint}")
        response.raise_for_status()
        return response.json()

    async def put(self, endpoint: str, data: BaseModel) -> ApiResponse:
        response = await self._client.put(
            f"{self.base_url}/{endpoint}", 
            json=data.model_dump(mode='json', exclude_none=True)
        )
        response.raise_for_status()
        return response.json()

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()