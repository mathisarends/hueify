from typing import Any, TypeVar
from pydantic import BaseModel
import httpx

from hueify.credentials import HueBridgeCredentials
from hueify.utils.logging import LoggingMixin

T = TypeVar('T', bound=BaseModel)


class HttpClient(LoggingMixin):
    def __init__(
        self, 
        credentials: HueBridgeCredentials | None = None,
        timeout: float = 10.0
    ) -> None:
        self._credentials = credentials or HueBridgeCredentials()
        self._timeout = timeout
        self._client: httpx.AsyncClient | None = None

    @property
    def base_url(self) -> str:
        if not self._credentials.hue_bridge_ip or not self._credentials.hue_user_id:
            raise ValueError("Credentials not properly configured")
        return f"http://{self._credentials.hue_bridge_ip}/api/{self._credentials.hue_user_id}"

    async def __aenter__(self):
        self._client = httpx.AsyncClient(timeout=self._timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()

    async def get(self, endpoint: str, response_model: type[T]) -> T:
        if not self._client:
            raise RuntimeError("Client must be used as context manager")
        response = await self._client.get(f"{self.base_url}/{endpoint}")
        response.raise_for_status()
        return response_model.model_validate(response.json())

    async def put(self, endpoint: str, data: BaseModel, response_model: type[T]) -> T:
        if not self._client:
            raise RuntimeError("Client must be used as context manager")
        response = await self._client.put(
            f"{self.base_url}/{endpoint}", 
            json=data.model_dump(mode='json', exclude_none=True)
        )
        response.raise_for_status()
        return response_model.model_validate(response.json())