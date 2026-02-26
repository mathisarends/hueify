from typing import TypeVar

import httpx
from pydantic import BaseModel, TypeAdapter

from hueify.credentials import HueBridgeCredentials
from hueify.http.schemas import ApiResponse, HueApiResponse

T = TypeVar("T", bound=BaseModel)


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
        self._client = httpx.AsyncClient(timeout=timeout, verify=verify_ssl)

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

    async def get_resources(self, endpoint: str, resource_type: type[T]) -> list[T]:
        response = await self._client.get(
            f"{self._base_url}/{self._normalize_endpoint(endpoint)}",
            headers=self._headers,
        )
        response.raise_for_status()

        adapter = TypeAdapter(HueApiResponse[resource_type])
        api_response = adapter.validate_python(response.json())
        return api_response.data

    async def get_resource(self, endpoint: str, resource_type: type[T]) -> T:
        response = await self._client.get(
            f"{self._base_url}/{self._normalize_endpoint(endpoint)}",
            headers=self._headers,
        )
        response.raise_for_status()

        adapter = TypeAdapter(HueApiResponse[resource_type])
        api_response = adapter.validate_python(response.json())
        return api_response.get_single_resource()

    async def put(
        self, endpoint: str, data: BaseModel, resource_type: type[T] | None = None
    ) -> ApiResponse | T:
        response = await self._client.put(
            f"{self._base_url}/{self._normalize_endpoint(endpoint)}",
            headers=self._headers,
            json=data.model_dump(mode="json", exclude_none=True),
        )
        response.raise_for_status()

        if resource_type is not None:
            adapter = TypeAdapter(HueApiResponse[resource_type])
            api_response = adapter.validate_python(response.json())
            return api_response.get_single_resource()

        return response.json()

    async def close(self) -> None:
        await self._client.aclose()

    def _normalize_endpoint(self, endpoint: str) -> str:
        return endpoint.lstrip("/")
