import asyncio

import httpx
from pydantic import BaseModel


class RegisteredApp(BaseModel):
    """What the bridge hands out when the link button is pressed.

    The application key authorizes the REST API and the event stream. The
    client key is the pre-shared key of the entertainment stream, and only
    exists because registration asks for it - the bridge never reveals it
    again.
    """

    app_key: str
    client_key: str | None = None


_POLL_INTERVAL = 2
_TIMEOUT_SECONDS = 60


async def register_app_key(
    bridge_ip: str, device_type: str = "hueify#setup"
) -> RegisteredApp:
    payload = {"devicetype": device_type, "generateclientkey": True}

    async with httpx.AsyncClient(verify=False) as client:
        for _ in range(_TIMEOUT_SECONDS // _POLL_INTERVAL):
            response = await client.post(f"https://{bridge_ip}/api", json=payload)
            result = response.json()[0]

            if success := result.get("success"):
                return RegisteredApp(
                    app_key=success["username"], client_key=success.get("clientkey")
                )

            await asyncio.sleep(_POLL_INTERVAL)

    raise TimeoutError("Link button was not pressed within 60 seconds.")
