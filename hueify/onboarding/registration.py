import asyncio

import httpx
from pydantic import BaseModel, TypeAdapter

from hueify.errors import BridgeError, HueifyError
from hueify.models import HueApiError


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
_LINK_BUTTON_NOT_PRESSED = 101


class _RegistrationSuccess(BaseModel):
    username: str
    clientkey: str | None = None


class _RegistrationError(HueApiError):
    type: int


class _RegistrationResult(BaseModel):
    success: _RegistrationSuccess | None = None
    error: _RegistrationError | None = None


_REGISTRATION_RESPONSE = TypeAdapter(list[_RegistrationResult])


async def register_app_key(
    bridge_ip: str, device_type: str = "hueify#setup"
) -> RegisteredApp:
    payload = {"devicetype": device_type, "generateclientkey": True}

    async with httpx.AsyncClient(verify=False) as client:
        for _ in range(_TIMEOUT_SECONDS // _POLL_INTERVAL):
            response = await client.post(f"https://{bridge_ip}/api", json=payload)
            response.raise_for_status()
            results = _REGISTRATION_RESPONSE.validate_python(response.json())
            errors = [result.error for result in results if result.error is not None]
            if any(error.type != _LINK_BUTTON_NOT_PRESSED for error in errors):
                raise BridgeError(errors)

            if not errors:
                for result in results:
                    if result.success is not None:
                        return RegisteredApp(
                            app_key=result.success.username,
                            client_key=result.success.clientkey,
                        )
                raise HueifyError("The bridge returned no registration result")

            await asyncio.sleep(_POLL_INTERVAL)

    raise TimeoutError("Link button was not pressed within 60 seconds.")
