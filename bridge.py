from __future__ import annotations

import os
from typing import Any, Optional
import aiohttp
from dotenv import load_dotenv

load_dotenv()

class HueBridge:
    """Base class for communication with the Hue Bridge."""
    
    # Default environment variable names
    ENV_USER_ID = "HUE_USER_ID"
    ENV_BRIDGE_IP = "HUE_BRIDGE_IP"

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
        Raises:
            ValueError: If no bridge is found or user ID isn't available
        """
        bridges = await BridgeDiscovery.discover_bridges()
        if not bridges:
            raise ValueError("No Hue Bridge found")

        user_id = os.getenv(cls.ENV_USER_ID)
        if not user_id:
            raise ValueError(f"No user ID found. Set {cls.ENV_USER_ID} environment variable.")

        return cls(ip=bridges[0]["internalipaddress"], user=user_id)

    @classmethod
    def connect_by_ip(
        cls, ip: Optional[str] = None, user_id: Optional[str] = None
    ) -> HueBridge:
        """
        Connects to a Hue Bridge using a specific IP address and user ID.
        Falls back to environment variables if parameters are not provided.
        """
        ip = ip or os.getenv(cls.ENV_BRIDGE_IP)
        user_id = user_id or os.getenv(cls.ENV_USER_ID)
        
        if not ip:
            raise ValueError(f"No IP address provided. Set {cls.ENV_BRIDGE_IP} environment variable or pass IP.")
        if not user_id:
            raise ValueError(f"No user ID provided. Set {cls.ENV_USER_ID} environment variable or pass user ID.")

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