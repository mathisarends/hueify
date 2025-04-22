from __future__ import annotations

import os
from typing import Any, Optional
import aiohttp
from dotenv import load_dotenv

load_dotenv()

class HueBridge:
    """
    Provides methods for interacting with a Philips Hue Bridge, including 
    connection management and HTTP communication via the Hue API.
    """

    ENV_USER_ID = "HUE_USER_ID"
    ENV_BRIDGE_IP = "HUE_BRIDGE_IP"

    def __init__(self, ip: str, user: str) -> None:
        """
        Create a HueBridge instance using a static IP address and user ID.

        Args:
            ip: The IP address of the Hue Bridge.
            user: The authorized user ID for the Hue API.
        """
        self.ip = ip
        self.user = user
    
    @staticmethod
    async def discover_bridges() -> list[dict[str, str]]:
        """
        Query the Philips Hue discovery service to find bridges in the local network.

        Returns:
            A list of bridge information dictionaries containing at least 'internalipaddress'.
        """
        async with aiohttp.ClientSession() as session:
            async with session.get("https://discovery.meethue.com/") as response:
                return await response.json()

    @property
    def url(self) -> str:
        """
        Construct the base API URL for the connected Hue Bridge.

        Returns:
            The full base URL for API communication.
        """
        return f"http://{self.ip}/api/{self.user}"

    @classmethod
    async def connect(cls) -> HueBridge:
        """
        Discover available Hue Bridges and connect to the first one using 
        credentials stored in environment variables.

        Returns:
            An instance of HueBridge.

        Raises:
            ValueError: If no bridge is found or required environment variables are missing.
        """
        bridges = await HueBridge.discover_bridges()
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
        Manually connect to a Hue Bridge using provided or environment-based credentials.

        Args:
            ip: Optional IP address of the Hue Bridge.
            user_id: Optional Hue API user ID.

        Returns:
            An instance of HueBridge.

        Raises:
            ValueError: If either the IP address or user ID is missing.
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
        Send an HTTP GET request to the specified Hue Bridge endpoint.

        Args:
            endpoint: Relative API endpoint to request.

        Returns:
            Parsed JSON response from the bridge.
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.url}/{endpoint}") as response:
                return await response.json()

    async def put_request(self, endpoint: str, data: dict) -> Any:
        """
        Send an HTTP PUT request with a JSON payload to the Hue Bridge.

        Args:
            endpoint: Relative API endpoint to update.
            data: Dictionary of data to send in the request body.

        Returns:
            Parsed JSON response from the bridge.
        """
        async with aiohttp.ClientSession() as session:
            async with session.put(f"{self.url}/{endpoint}", json=data) as response:
                return await response.json()
            
    def __repr__(self) -> str:
        """
        Return a short representation of the HueBridge instance.
        """
        return f"<HueBridge {self.ip}>"