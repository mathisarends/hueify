from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import httpx
import pytest
from pydantic import TypeAdapter

from hueify.credentials import HueBridgeCredentials
from hueify.http import HttpClient
from hueify.models import HueApiResponse, Light, LightUpdate, OnState, ResourceType

VALID_IP = "192.168.1.100"
VALID_APP_KEY = "a" * 40


@pytest.fixture
def credentials() -> HueBridgeCredentials:
    return HueBridgeCredentials(HUE_BRIDGE_IP=VALID_IP, HUE_APP_KEY=VALID_APP_KEY)


@pytest.fixture
def http_client(credentials: HueBridgeCredentials) -> HttpClient:
    return HttpClient(credentials=credentials)


def response_with(payload: dict) -> MagicMock:
    response = MagicMock()
    response.json.return_value = payload
    return response


def light_response() -> dict:
    return {
        "errors": [],
        "data": [
            {
                "id": str(uuid4()),
                "type": "light",
                "owner": {"rid": str(uuid4()), "rtype": "device"},
                "metadata": {"name": "Desk", "archetype": "table_shade"},
                "on": {"on": True},
                "new_hue_field": {"preserved": True},
            }
        ],
    }


def write_response(resource_type: ResourceType = ResourceType.LIGHT) -> dict:
    return {
        "errors": [],
        "data": [{"rid": str(uuid4()), "rtype": resource_type.value}],
    }


def test_base_url_and_headers(http_client: HttpClient) -> None:
    assert http_client._base_url == f"https://{VALID_IP}/clip/v2/resource"
    assert http_client._headers["hue-application-key"] == VALID_APP_KEY
    assert http_client._headers["Content-Type"] == "application/json"


@pytest.mark.asyncio
async def test_get_returns_typed_resource_and_preserves_extra_fields(
    http_client: HttpClient,
) -> None:
    with patch.object(http_client._client, "get", new_callable=AsyncMock) as get:
        get.return_value = response_with(light_response())

        result = await http_client.get("light/id", TypeAdapter(HueApiResponse[Light]))

    assert isinstance(result.data[0], Light)
    assert result.data[0].model_extra == {"new_hue_field": {"preserved": True}}
    assert get.await_args is not None
    assert get.await_args.kwargs["headers"]["hue-application-key"] == VALID_APP_KEY
    assert get.await_args.args[0].endswith("/clip/v2/resource/light/id")


@pytest.mark.asyncio
async def test_get_raises_on_http_error(http_client: HttpClient) -> None:
    response = MagicMock()
    response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "not found", request=MagicMock(), response=MagicMock()
    )
    with patch.object(http_client._client, "get", new_callable=AsyncMock) as get:
        get.return_value = response

        with pytest.raises(httpx.HTTPStatusError):
            await http_client.get("light/missing", TypeAdapter(HueApiResponse[Light]))


@pytest.mark.asyncio
async def test_put_serializes_typed_request_and_returns_typed_identifiers(
    http_client: HttpClient,
) -> None:
    update = LightUpdate(on=OnState(on=True))
    with patch.object(http_client._client, "put", new_callable=AsyncMock) as put:
        put.return_value = response_with(write_response())

        result = await http_client.put("light/id", update)

    assert put.await_args is not None
    assert put.await_args.kwargs["json"] == {"on": {"on": True}}
    assert result.data[0].rtype is ResourceType.LIGHT


@pytest.mark.asyncio
async def test_post_uses_collection_endpoint(http_client: HttpClient) -> None:
    update = LightUpdate(on=OnState(on=True))
    with patch.object(http_client._client, "post", new_callable=AsyncMock) as post:
        post.return_value = response_with(write_response())

        await http_client.post("light", update)

    assert post.await_args is not None
    assert post.await_args.args[0].endswith("/clip/v2/resource/light")


@pytest.mark.asyncio
async def test_delete_returns_typed_identifiers(http_client: HttpClient) -> None:
    with patch.object(http_client._client, "delete", new_callable=AsyncMock) as delete:
        delete.return_value = response_with(write_response())

        result = await http_client.delete("light/id")

    assert result.data[0].rtype is ResourceType.LIGHT


@pytest.mark.asyncio
async def test_context_manager_closes_client(
    credentials: HueBridgeCredentials,
) -> None:
    with patch.object(httpx.AsyncClient, "aclose", new_callable=AsyncMock) as close:
        async with HttpClient(credentials=credentials):
            pass

    close.assert_awaited_once()
