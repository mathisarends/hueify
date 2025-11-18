from typing import Self

import httpx

from hueify.bridge.exceptions import (
    BridgeConnectionException,
    BridgeNotFoundException,
)
from hueify.bridge.models import BridgeListAdapter, DisoveredBrigeResponse
from hueify.credentials import HueBridgeCredentials
from hueify.utils.logging import LoggingMixin


class HueBridge(LoggingMixin):
    def __init__(self, ip: str, hue_app_key: str) -> None:
        self._ip = ip
        self._hue_app_key = hue_app_key

    @staticmethod
    async def discover_bridges() -> list[DisoveredBrigeResponse]:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://discovery.meethue.com/", timeout=10.0
                )
                response.raise_for_status()
                return BridgeListAdapter.validate_python(response.json())
        except httpx.HTTPError as e:
            raise BridgeConnectionException(f"Failed to discover bridges: {e!s}") from e

    @property
    def base_url(self) -> str:
        return f"http://{self._ip}/api/{self._hue_app_key}"

    @property
    def ip(self) -> str:
        return self._ip

    @property
    def hue_app_key(self) -> str:
        return self._hue_app_key

    @classmethod
    async def connect(cls) -> Self:
        credentials = HueBridgeCredentials()

        if credentials.hue_bridge_ip and credentials.hue_app_key:
            return cls(
                ip=credentials.hue_bridge_ip, hue_user_id=credentials.hue_app_key
            )

        return await cls._connect_with_discovery(credentials)

    @classmethod
    async def _connect_with_discovery(cls, credentials: HueBridgeCredentials) -> Self:
        bridges = await cls.discover_bridges()
        if not bridges:
            raise BridgeNotFoundException()

        if not credentials.hue_app_key:
            raise BridgeConnectionException(
                "HUE_APP_KEY environment variable is required"
            )

        return cls(ip=bridges[0].internalipaddress, hue_user_id=credentials.hue_app_key)
