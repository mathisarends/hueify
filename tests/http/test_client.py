from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from pydantic import BaseModel

from hueify.credentials import HueBridgeCredentials
from hueify.http.client import HttpClient


class MockResource(BaseModel):
    id: str
    name: str


class ResourceWithOptional(BaseModel):
    id: str
    optional_field: str | None = None


@pytest.fixture
def credentials() -> HueBridgeCredentials:
    creds = HueBridgeCredentials()
    creds.hue_bridge_ip = "192.168.1.100"
    creds.hue_app_key = "a" * 40
    return creds


@pytest.fixture
def http_client(credentials: HueBridgeCredentials) -> HttpClient:
    return HttpClient(credentials=credentials)


def test_initializes_with_provided_credentials(
    credentials: HueBridgeCredentials,
) -> None:
    client = HttpClient(credentials=credentials)
    assert client._credentials == credentials


def test_initializes_with_default_credentials() -> None:
    client = HttpClient(
        credentials=HueBridgeCredentials(
            hue_bridge_ip="192.168.1.1", hue_app_key="a" * 40
        )
    )
    assert client._credentials is not None


def test_base_url_construction(http_client: HttpClient) -> None:
    expected = "https://192.168.1.100/clip/v2/resource"
    assert http_client.base_url == expected


def test_base_url_raises_without_ip(credentials: HueBridgeCredentials) -> None:
    credentials.hue_bridge_ip = None
    client = HttpClient(credentials=credentials)
    with pytest.raises(ValueError, match="missing IP"):
        _ = client.base_url


def test_headers_construction(http_client: HttpClient) -> None:
    headers = http_client._headers
    assert headers["hue-application-key"] == "a" * 40
    assert headers["Content-Type"] == "application/json"


def test_headers_raises_without_app_key(
    credentials: HueBridgeCredentials,
) -> None:
    credentials.hue_app_key = None
    client = HttpClient(credentials=credentials)
    with pytest.raises(ValueError, match="missing App Key"):
        _ = client._headers


@pytest.mark.asyncio
async def test_get_returns_api_response(http_client: HttpClient) -> None:
    mock_response_dict = {"errors": [], "data": [{"id": "1", "name": "Light"}]}

    mock_response = MagicMock()
    mock_response.json.return_value = mock_response_dict
    mock_response.raise_for_status = MagicMock()

    with patch.object(http_client._client, "get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        result = await http_client.get("light/1")

    assert result == mock_response_dict
    mock_get.assert_called_once()


@pytest.mark.asyncio
async def test_get_uses_correct_url(http_client: HttpClient) -> None:
    mock_response = MagicMock()
    mock_response.json.return_value = {"errors": [], "data": []}
    mock_response.raise_for_status = MagicMock()

    with patch.object(http_client._client, "get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        await http_client.get("light/1")

    call_args = mock_get.call_args
    assert "https://192.168.1.100/clip/v2/resource/light/1" in str(call_args)


@pytest.mark.asyncio
async def test_get_includes_headers(http_client: HttpClient) -> None:
    mock_response = MagicMock()
    mock_response.json.return_value = {"errors": [], "data": []}
    mock_response.raise_for_status = MagicMock()

    with patch.object(http_client._client, "get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        await http_client.get("light/1")

    call_kwargs = mock_get.call_args.kwargs
    assert "headers" in call_kwargs
    assert call_kwargs["headers"]["hue-application-key"] == "a" * 40


@pytest.mark.asyncio
async def test_get_raises_on_http_error(http_client: HttpClient) -> None:
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = Exception("404 Not Found")

    with patch.object(http_client._client, "get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response

        with pytest.raises(Exception, match="404 Not Found"):
            await http_client.get("light/nonexistent")


@pytest.mark.asyncio
async def test_get_resource_returns_parsed_resource(http_client: HttpClient) -> None:
    mock_response_dict = {
        "errors": [],
        "data": [{"id": "test-id", "name": "Test Light"}],
    }

    mock_response = MagicMock()
    mock_response.json.return_value = mock_response_dict
    mock_response.raise_for_status = MagicMock()

    with patch.object(http_client._client, "get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        result = await http_client.get_resource("light/1", MockResource)

    assert isinstance(result, MockResource)
    assert result.id == "test-id"
    assert result.name == "Test Light"


@pytest.mark.asyncio
async def test_get_resource_raises_on_empty_data(http_client: HttpClient) -> None:
    mock_response_dict = {"errors": [], "data": []}

    mock_response = MagicMock()
    mock_response.json.return_value = mock_response_dict
    mock_response.raise_for_status = MagicMock()

    with patch.object(http_client._client, "get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response

        with pytest.raises(ValueError, match="No resource found"):
            await http_client.get_resource("light/nonexistent", MockResource)


@pytest.mark.asyncio
async def test_get_resource_validates_response_schema(http_client: HttpClient) -> None:
    mock_response_dict = {
        "errors": [],
        "data": [{"id": "test-id", "name": "Test Light"}],
    }

    mock_response = MagicMock()
    mock_response.json.return_value = mock_response_dict
    mock_response.raise_for_status = MagicMock()

    with patch.object(http_client._client, "get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        result = await http_client.get_resource("light/1", MockResource)

    assert result.id == "test-id"


@pytest.mark.asyncio
async def test_put_sends_data_as_json(http_client: HttpClient) -> None:
    test_data = MockResource(id="1", name="Updated Light")
    mock_response_dict = {"errors": [], "data": []}

    mock_response = MagicMock()
    mock_response.json.return_value = mock_response_dict
    mock_response.raise_for_status = MagicMock()

    with patch.object(http_client._client, "put", new_callable=AsyncMock) as mock_put:
        mock_put.return_value = mock_response
        await http_client.put("light/1", test_data)

    call_kwargs = mock_put.call_args.kwargs
    assert "json" in call_kwargs
    assert call_kwargs["json"]["id"] == "1"
    assert call_kwargs["json"]["name"] == "Updated Light"


@pytest.mark.asyncio
async def test_put_excludes_none_values(http_client: HttpClient) -> None:
    test_data = ResourceWithOptional(id="1", optional_field=None)
    mock_response_dict = {"errors": [], "data": []}

    mock_response = MagicMock()
    mock_response.json.return_value = mock_response_dict
    mock_response.raise_for_status = MagicMock()

    with patch.object(http_client._client, "put", new_callable=AsyncMock) as mock_put:
        mock_put.return_value = mock_response
        await http_client.put("light/1", test_data)

    call_kwargs = mock_put.call_args.kwargs
    assert "optional_field" not in call_kwargs["json"]


@pytest.mark.asyncio
async def test_put_uses_correct_url(http_client: HttpClient) -> None:
    test_data = MockResource(id="1", name="Light")
    mock_response_dict = {"errors": [], "data": []}

    mock_response = MagicMock()
    mock_response.json.return_value = mock_response_dict
    mock_response.raise_for_status = MagicMock()

    with patch.object(http_client._client, "put", new_callable=AsyncMock) as mock_put:
        mock_put.return_value = mock_response
        await http_client.put("light/1", test_data)

    call_args = mock_put.call_args
    assert "https://192.168.1.100/clip/v2/resource/light/1" in str(call_args)


@pytest.mark.asyncio
async def test_put_includes_headers(http_client: HttpClient) -> None:
    test_data = MockResource(id="1", name="Light")
    mock_response_dict = {"errors": [], "data": []}

    mock_response = MagicMock()
    mock_response.json.return_value = mock_response_dict
    mock_response.raise_for_status = MagicMock()

    with patch.object(http_client._client, "put", new_callable=AsyncMock) as mock_put:
        mock_put.return_value = mock_response
        await http_client.put("light/1", test_data)

    call_kwargs = mock_put.call_args.kwargs
    assert "headers" in call_kwargs
    assert call_kwargs["headers"]["Content-Type"] == "application/json"


@pytest.mark.asyncio
async def test_put_raises_on_http_error(http_client: HttpClient) -> None:
    test_data = MockResource(id="1", name="Light")
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = Exception("400 Bad Request")

    with patch.object(http_client._client, "put", new_callable=AsyncMock) as mock_put:
        mock_put.return_value = mock_response

        with pytest.raises(Exception, match="400 Bad Request"):
            await http_client.put("light/1", test_data)


@pytest.mark.asyncio
async def test_context_manager_closes_client(
    credentials: HueBridgeCredentials,
) -> None:
    with patch.object(
        httpx.AsyncClient, "aclose", new_callable=AsyncMock
    ) as mock_close:
        async with HttpClient(credentials=credentials) as client:
            assert client is not None

        mock_close.assert_called_once()


@pytest.mark.asyncio
async def test_context_manager_manual_close(
    credentials: HueBridgeCredentials,
) -> None:
    client = HttpClient(credentials=credentials)
    with patch.object(client._client, "aclose", new_callable=AsyncMock) as mock_close:
        await client.close()

    mock_close.assert_called_once()
