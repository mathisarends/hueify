from __future__ import annotations

import asyncio
import os
from typing import Any, Optional

import aiohttp
from dotenv import load_dotenv

class HueBridge:
    """Base class for communication with the Hue Bridge."""

    def __init__(self, ip: str, user: str) -> None:
        """
        Initializes the HueBridge with an IP address and a user ID.
        """
        self.ip = ip
        self.user = user

    def __repr__(self) -> str:
        """
        Returns a string representation of the HueBridge.
        """
        return f"<HueBridge {self.ip}>"

    @property
    def url(self) -> str:
        """
        Returns the base URL for API requests.
        """
        return f"http://{self.ip}/api/{self.user}"

    @classmethod
    async def connect(cls) -> HueBridge:
        """
        Connects to the first discovered Hue Bridge using stored credentials.
        """
        bridges = await BridgeDiscovery.discover_bridges()
        if not bridges:
            raise ValueError("No Hue Bridge found")

        ip, user_id = BridgeDiscovery.get_credentials()
        return cls(ip=bridges[0]["internalipaddress"], user=user_id)

    @classmethod
    def connect_by_ip(
        cls, ip: Optional[str] = None, user_id: Optional[str] = None
    ) -> HueBridge:
        """
        Connects to a Hue Bridge using a specific IP address and user ID.
        """
        if ip is None or user_id is None:
            fallback_ip, fallback_user = BridgeDiscovery.get_credentials()
            ip = ip or fallback_ip
            user_id = user_id or fallback_user

        return cls(ip=ip, user=user_id)

    async def get_request(self, endpoint: str) -> Any:
        """
        Sends a GET request to the Hue Bridge.
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.url}/{endpoint}") as response:
                return await response.json()

    async def put_request(self, endpoint: str, data: dict) -> Any:
        """
        Sends a PUT request with data to the Hue Bridge.
        """
        async with aiohttp.ClientSession() as session:
            async with session.put(f"{self.url}/{endpoint}", json=data) as response:
                return await response.json()



class BridgeDiscovery:
    """Responsible for discovering and configuring Hue Bridges."""

    @staticmethod
    async def discover_bridges() -> list[dict[str, str]]:
        """
        Discovers available Hue Bridges on the local network.
        """
        async with aiohttp.ClientSession() as session:
            async with session.get("https://discovery.meethue.com/") as response:
                return await response.json()

    @staticmethod
    def get_credentials() -> tuple[str, str]:
        """
        Loads the Hue Bridge IP and user ID from environment variables.
        """
        load_dotenv()
        bridge_ip = os.getenv("HUE_BRIDGE_IP")
        user_id = os.getenv("HUE_USER_ID")

        if not user_id:
            raise ValueError("HUE_USER_ID not found in .env file")

        return bridge_ip, user_id