import asyncio

import httpx
from pydantic import BaseModel


class AppKeyResponse(BaseModel):
    username: str


_POLL_INTERVAL = 2
_TIMEOUT_SECONDS = 60


async def register_app_key(bridge_ip: str, device_type: str = "hueify#cli") -> str:
    url = f"http://{bridge_ip}/api"
    payload = {"devicetype": device_type, "generateclientkey": True}

    async with httpx.AsyncClient(verify=False) as client:
        for _ in range(_TIMEOUT_SECONDS // _POLL_INTERVAL):
            response = await client.post(url, json=payload)
            result = response.json()[0]

            if "success" in result:
                return result["success"]["username"]

            await asyncio.sleep(_POLL_INTERVAL)

    raise TimeoutError("Link button was not pressed within 60 seconds.")
