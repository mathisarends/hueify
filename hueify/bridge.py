from __future__ import annotations

import os
from typing import Optional
import httpx
from dotenv import load_dotenv

load_dotenv()


class HueBridge:
    HUE_USER_ID = "HUE_USER_ID"
    ENV_BRIDGE_IP = "HUE_BRIDGE_IP"

    def __init__(self, ip: str, user: str) -> None:
        self.ip = ip
        self.user = user

    @staticmethod
    async def discover_bridges() -> list[dict[str, str]]:
        async with httpx.AsyncClient() as client:
            response = await client.get("https://discovery.meethue.com/")
            return response.json()

    @property
    def base_url(self) -> str:
        return f"http://{self.ip}/api/{self.user}"

    @classmethod
    async def connect(cls) -> HueBridge:
        bridges = await HueBridge.discover_bridges()
        if not bridges:
            raise ValueError("No Hue Bridge found")

        user_id = os.getenv(cls.HUE_USER_ID)
        if not user_id:
            raise ValueError(
                f"No user ID found. Set {cls.HUE_USER_ID} environment variable."
            )

        return cls(ip=bridges[0]["internalipaddress"], user=user_id)

    @classmethod
    def connect_by_ip(
        cls, ip: Optional[str] = None, user_id: Optional[str] = None
    ) -> HueBridge:
        ip = ip or os.getenv(cls.ENV_BRIDGE_IP)
        user_id = user_id or os.getenv(cls.HUE_USER_ID)

        if not ip:
            raise ValueError(
                f"No IP address provided. Set {cls.ENV_BRIDGE_IP} environment variable or pass IP."
            )
        if not user_id:
            raise ValueError(
                f"No user ID provided. Set {cls.HUE_USER_ID} environment variable or pass user ID."
            )

        return cls(ip=ip, user=user_id)

    def __repr__(self) -> str:
        return f"<HueBridge {self.ip}>"
