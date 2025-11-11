from typing import Self
import httpx

from hueify.bridge.models import DisoveredBrigeResponse, BridgeListAdapter
from hueify.utils.logging import LoggingMixin
from hueify.credentials import HueBridgeCredentials

from hueify.bridge.exceptions import (
    BridgeNotFoundException, 
    BridgeConnectionException, 
)

class HueBridge(LoggingMixin):
    def __init__(self, ip: str, hue_user_id: str) -> None:
        self._ip = ip
        self._hue_user_id = hue_user_id

    @staticmethod
    async def discover_bridges() -> list[DisoveredBrigeResponse]:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("https://discovery.meethue.com/", timeout=10.0)
                response.raise_for_status()
                return BridgeListAdapter.validate_python(response.json())
        except httpx.HTTPError as e:
            raise BridgeConnectionException(f"Failed to discover bridges: {str(e)}")

    @property
    def base_url(self) -> str:
        return f"http://{self._ip}/api/{self._hue_user_id}"

    @property
    def ip(self) -> str:
        return self._ip

    @property
    def hue_user_id(self) -> str:
        return self._hue_user_id

    @classmethod
    async def connect(cls) -> Self:
        credentials = HueBridgeCredentials()
        
        if credentials.hue_bridge_ip and credentials.hue_user_id:
            return cls(ip=credentials.hue_bridge_ip, hue_user_id=credentials.hue_user_id)
        
        return await cls._connect_with_discovery(credentials)

    @classmethod
    async def _connect_with_discovery(cls, credentials: HueBridgeCredentials) -> Self:
        bridges = await cls.discover_bridges()
        if not bridges:
            raise BridgeNotFoundException()

        if not credentials.hue_user_id:
            raise BridgeConnectionException("HUE_USER_ID environment variable is required")

        return cls(ip=bridges[0].internalipaddress, hue_user_id=credentials.hue_user_id)