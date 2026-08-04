from collections.abc import Mapping
from typing import Any

import httpx

from hueify.credentials import HueBridgeCredentials
from hueify.http.schemas import ApiResponse


class HttpClient:
    _HUE_API_BASE_PATH = "/clip/v2/resource"

    def __init__(
        self,
        credentials: HueBridgeCredentials,
        timeout: float = 10.0,
        verify_ssl: bool = False,
    ) -> None:
        self._base_url = f"https://{credentials.hue_bridge_ip}{self._HUE_API_BASE_PATH}"
        self._headers = {
            "hue-application-key": credentials.hue_app_key,
            "Content-Type": "application/json",
        }
        self._client = httpx.AsyncClient(timeout=timeout, verify=verify_ssl, http2=True)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def get(self, endpoint: str) -> ApiResponse:
        response = await self._client.get(
            f"{self._base_url}/{self._normalize_endpoint(endpoint)}",
            headers=self._headers,
        )
        response.raise_for_status()
        return response.json()

    async def post(self, endpoint: str, data: Mapping[str, Any]) -> ApiResponse:
        response = await self._client.post(
            f"{self._base_url}/{self._normalize_endpoint(endpoint)}",
            headers=self._headers,
            json=dict(data),
        )
        response.raise_for_status()
        return response.json()

    async def put(self, endpoint: str, data: Mapping[str, Any]) -> ApiResponse:
        response = await self._client.put(
            f"{self._base_url}/{self._normalize_endpoint(endpoint)}",
            headers=self._headers,
            json=dict(data),
        )
        response.raise_for_status()
        return response.json()

    async def delete(self, endpoint: str) -> ApiResponse:
        response = await self._client.delete(
            f"{self._base_url}/{self._normalize_endpoint(endpoint)}",
            headers=self._headers,
        )
        response.raise_for_status()
        return response.json()

    async def close(self) -> None:
        await self._client.aclose()

    def _normalize_endpoint(self, endpoint: str) -> str:
        return endpoint.lstrip("/")
