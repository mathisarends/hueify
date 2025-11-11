import httpx
from pydantic import BaseModel

from hueify.credentials import HueBridgeCredentials
from hueify.http.models import ApiResponse
from hueify.utils.logging import LoggingMixin


class HttpClient(LoggingMixin):
    def __init__(
        self,
        credentials: HueBridgeCredentials | None = None,
        timeout: float = 10.0,
        verify_ssl: bool = False,
    ) -> None:
        self._credentials = credentials or HueBridgeCredentials()
        self._client = httpx.AsyncClient(timeout=timeout, verify=verify_ssl)

    @property
    def base_url(self) -> str:
        if not self._credentials.hue_bridge_ip:
            raise ValueError("Credentials not properly configured (missing IP)")
        return f"https://{self._credentials.hue_bridge_ip}/clip/v2/resource"

    @property
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
