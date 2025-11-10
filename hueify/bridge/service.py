import os
from typing import Self
import httpx
from dotenv import load_dotenv

from hueify.bridge.models import BridgeDiscoveryResponse, BridgeListAdapter

from hueify.bridge.exceptions import (
    BridgeNotFoundException, 
    BridgeConnectionException, 
    MissingCredentialsException
)

load_dotenv(override=True)


class HueBridge:
    HUE_USER_ID = "HUE_USER_ID"
    ENV_BRIDGE_IP = "HUE_BRIDGE_IP"

    def __init__(self, ip: str, user: str) -> None:
        self.ip = ip
        self.user = user

    @staticmethod
    def _get_bridge_ip_from_env_or_raise(ip: str | None = None) -> str:
        if ip:
            return ip
        value = os.getenv(HueBridge.ENV_BRIDGE_IP)
        if not value:
            raise MissingCredentialsException(f"IP address ({HueBridge.ENV_BRIDGE_IP} environment variable)")
        return value

    @staticmethod
    def _get_user_id_from_env_or_raise(user_id: str | None = None) -> str:
        if user_id:
            return user_id
        value = os.getenv(HueBridge.HUE_USER_ID)
        if not value:
            raise MissingCredentialsException(f"user ID ({HueBridge.HUE_USER_ID} environment variable)")
        return value

    @staticmethod
    async def discover_bridges() -> list[BridgeDiscoveryResponse]:
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

    @classmethod
    async def connect(cls) -> Self:
        bridges = await cls.discover_bridges()
        if not bridges:
            raise BridgeNotFoundException()

        user_id = cls._get_user_id_from_env_or_raise()
        return cls(ip=bridges[0]["internalipaddress"], user=user_id)

    @classmethod
    def connect_by_ip_and_user_id(
        cls, ip: str | None = None, user_id: str | None = None
    ) -> Self:
        bridge_ip = cls._get_bridge_ip_from_env_or_raise(ip)
        bridge_user_id = cls._get_user_id_from_env_or_raise(user_id)
        return cls(ip=bridge_ip, user=bridge_user_id)