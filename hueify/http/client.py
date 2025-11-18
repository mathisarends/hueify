from functools import cached_property
from typing import TypeVar

import httpx
from pydantic import BaseModel, TypeAdapter

from hueify.credentials import HueBridgeCredentials
from hueify.http.models import ApiResponse, HueApiResponse

T = TypeVar("T", bound=BaseModel)


class HttpClient:
    def __init__(
        self,
        credentials: HueBridgeCredentials | None = None,
        timeout: float = 10.0,
        verify_ssl: bool = False,
    ) -> None:
        self._credentials = credentials or HueBridgeCredentials()
        self._client = httpx.AsyncClient(timeout=timeout, verify=verify_ssl)

    @cached_property
    def base_url(self) -> str:
        if not self._credentials.hue_bridge_ip:
            raise ValueError("Credentials not properly configured (missing IP)")
        return f"https://{self._credentials.hue_bridge_ip}/clip/v2/resource"

    @cached_property
    def _headers(self) -> dict[str, str]:
        if not self._credentials.hue_app_key:
            raise ValueError("Credentials not properly configured (missing App Key)")
        return {
            "hue-application-key": self._credentials.hue_app_key,
            "Content-Type": "application/json",
        }

    async def get(self, endpoint: str) -> ApiResponse:
        response = await self._client.get(
            f"{self.base_url}/{endpoint}", headers=self._headers
        )
        response.raise_for_status()
        return response.json()

    async def get_resources(self, endpoint: str, resource_type: type[T]) -> list[T]:
        response = await self._client.get(
            f"{self.base_url}/{endpoint}", headers=self._headers
        )
        response.raise_for_status()

        adapter = TypeAdapter(HueApiResponse[resource_type])
        api_response = adapter.validate_python(response.json())
        return api_response.data

    async def get_resource(self, endpoint: str, resource_type: type[T]) -> T:
        response = await self._client.get(
            f"{self.base_url}/{endpoint}", headers=self._headers
        )

        response.raise_for_status()

        adapter = TypeAdapter(HueApiResponse[resource_type])
        api_response = adapter.validate_python(response.json())
        return api_response.get_single_resource()

    async def put(self, endpoint: str, data: BaseModel) -> ApiResponse:
        response = await self._client.put(
            f"{self.base_url}/{endpoint}",
            headers=self._headers,
            json=data.model_dump(mode="json", exclude_none=True),
        )
        response.raise_for_status()
        return response.json()

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
