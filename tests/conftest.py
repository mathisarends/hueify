import httpx
import pytest
import pytest_asyncio

from hueify import Hueify


@pytest.fixture
def without_stored_credentials(tmp_path, monkeypatch):
    """Hide the environment and any ``.env`` in the working directory."""
    monkeypatch.delenv("HUE_BRIDGE_IP", raising=False)
    monkeypatch.delenv("HUE_APP_KEY", raising=False)
    monkeypatch.delenv("HUE_CLIENT_KEY", raising=False)
    monkeypatch.chdir(tmp_path)


@pytest_asyncio.fixture
async def bridge():
    requests: list[httpx.Request] = []
    responses: list[dict | int] = []

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        result = responses.pop(0)
        return httpx.Response(
            result if isinstance(result, int) else 200,
            json={} if isinstance(result, int) else result,
        )

    async with Hueify(bridge_ip="192.168.1.10", app_key="a" * 40) as hue:
        await hue._http_client._client.aclose()
        hue._http_client._client = httpx.AsyncClient(
            transport=httpx.MockTransport(respond)
        )
        yield hue, requests, responses
        assert not responses, "Expected HTTP responses were not consumed"
