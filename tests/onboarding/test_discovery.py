from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from hueify.onboarding.discovery import DiscoveredBridge, discover_bridges


def response_with(payload: list) -> MagicMock:
    response = MagicMock()
    response.json.return_value = payload
    return response


@pytest.mark.asyncio
async def test_discover_bridges_returns_typed_bridges() -> None:
    payload = [{"id": "abc123", "internalipaddress": "192.168.1.50"}]
    with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as get:
        get.return_value = response_with(payload)

        bridges = await discover_bridges()

    assert bridges == [DiscoveredBridge(id="abc123", internalipaddress="192.168.1.50")]
    assert get.await_args.args[0] == "https://discovery.meethue.com/"


@pytest.mark.asyncio
async def test_discover_bridges_raises_when_none_are_found() -> None:
    with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as get:
        get.return_value = response_with([])

        with pytest.raises(RuntimeError, match="No Hue Bridge found"):
            await discover_bridges()


@pytest.mark.asyncio
async def test_discover_bridges_propagates_http_errors() -> None:
    response = MagicMock()
    response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "service unavailable", request=MagicMock(), response=MagicMock()
    )
    with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as get:
        get.return_value = response

        with pytest.raises(httpx.HTTPStatusError):
            await discover_bridges()
