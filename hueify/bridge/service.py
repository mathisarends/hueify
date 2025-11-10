import os
from typing import Self, overload
import httpx
from dotenv import load_dotenv

from hueify.bridge.models import DisoveredBrigeResponse, BridgeListAdapter
from hueify.utils.logging import LoggingMixin
from hueify.bridge.utils import (
    is_valid_ip, 
    is_valid_user_id,
)

from hueify.bridge.exceptions import (
    BridgeNotFoundException, 
    BridgeConnectionException, 
)

load_dotenv(override=True)


class HueBridge(LoggingMixin):
    HUE_USER_ID = "HUE_USER_ID"
    ENV_BRIDGE_IP = "HUE_BRIDGE_IP"

    def __init__(self, ip: str, user: str) -> None:
        self.ip = ip
        self.user = user

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
        return f"http://{self.ip}/api/{self.user}"

    @overload
    @classmethod
    async def connect(cls) -> Self:
        ...

    @overload
    @classmethod
    def connect(cls, bridge_ip: str, bridge_user_id: str) -> Self:
        ...

    @classmethod
    async def connect(cls, bridge_ip: str | None = None, bridge_user_id: str | None = None) -> Self:
        if bridge_ip and bridge_user_id:
            return cls._connect_with_credentials(bridge_ip, bridge_user_id)
        
        return await cls._connect_with_discovery()

    @classmethod
    def _connect_with_credentials(cls, bridge_ip: str, bridge_user_id: str) -> Self:
        cls._validate_credentials(bridge_ip, bridge_user_id)
        return cls(ip=bridge_ip, user=bridge_user_id)

    @classmethod
    async def _connect_with_discovery(cls) -> Self:
        bridges = await cls.discover_bridges()
        if not bridges:
            raise BridgeNotFoundException()

        user_id = os.getenv(cls.HUE_USER_ID)
        if not user_id:
            raise BridgeConnectionException(f"No {cls.HUE_USER_ID} found in environment")
            
        return cls(ip=bridges[0].internalipaddress, user=user_id)

    @classmethod
    def _validate_credentials(cls, ip: str, user_id: str) -> None:
        if not is_valid_ip(ip):
            cls.logger.warning(
                f"Provided IP address '{ip}' does not look like a valid IP address (format: xxx.xxx.xxx.xxx)"
            )
        
        if not is_valid_user_id(user_id):
            cls.logger.warning(
                f"Provided user ID '{user_id}' does not look like a valid Hue API user ID "
                f"(expected: alphanumeric, min 20 chars)"
            )