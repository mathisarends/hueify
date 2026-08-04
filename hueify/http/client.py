import httpx
from pydantic import BaseModel, TypeAdapter

from hueify.credentials import HueBridgeCredentials
from hueify.models import HueApiResponse, ResourceIdentifier


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

    async def get[T: BaseModel](
        self,
        endpoint: str,
        response_adapter: TypeAdapter[HueApiResponse[T]],
    ) -> HueApiResponse[T]:
        response = await self._client.get(self._url(endpoint), headers=self._headers)
        response.raise_for_status()
        return response_adapter.validate_python(response.json())

    async def post(
        self, endpoint: str, data: BaseModel
    ) -> HueApiResponse[ResourceIdentifier]:
        response = await self._client.post(
            self._url(endpoint),
            headers=self._headers,
            json=data.model_dump(mode="json", exclude_none=True),
        )
        response.raise_for_status()
        return self._validate_write_response(response.json())

    async def put(
        self, endpoint: str, data: BaseModel
    ) -> HueApiResponse[ResourceIdentifier]:
        response = await self._client.put(
            self._url(endpoint),
            headers=self._headers,
            json=data.model_dump(mode="json", exclude_none=True),
        )
        response.raise_for_status()
        return self._validate_write_response(response.json())

    async def delete(self, endpoint: str) -> HueApiResponse[ResourceIdentifier]:
        response = await self._client.delete(self._url(endpoint), headers=self._headers)
        response.raise_for_status()
        return self._validate_write_response(response.json())

    async def close(self) -> None:
        await self._client.aclose()

    def _url(self, endpoint: str) -> str:
        return f"{self._base_url}/{endpoint.lstrip('/')}"

    def _validate_write_response(
        self, response: object
    ) -> HueApiResponse[ResourceIdentifier]:
        return TypeAdapter(HueApiResponse[ResourceIdentifier]).validate_python(response)
