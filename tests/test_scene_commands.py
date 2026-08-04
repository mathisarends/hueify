from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from hueify.http import HttpClient
from hueify.models import HueApiResponse, ResourceIdentifier, SceneRecallRequest
from hueify.resources import SceneNamespace

SCENE_ID = UUID("88888888-8888-8888-8888-888888888888")


@pytest.fixture
def client() -> AsyncMock:
    http_client = AsyncMock(spec=HttpClient)
    http_client.put.return_value = HueApiResponse[ResourceIdentifier]()
    return http_client


def sent_recall(client: AsyncMock) -> dict:
    endpoint, request = client.put.await_args.args
    assert endpoint == f"scene/{SCENE_ID}"
    assert isinstance(request, SceneRecallRequest)
    return request.model_dump(mode="json", exclude_none=True)


@pytest.mark.asyncio
async def test_activate_recalls_the_scene_as_it_was_stored(client: AsyncMock) -> None:
    await SceneNamespace(client).activate(SCENE_ID)

    assert sent_recall(client) == {"recall": {"action": "active"}}


@pytest.mark.asyncio
async def test_activate_can_dim_and_fade_the_scene(client: AsyncMock) -> None:
    await SceneNamespace(client).activate(SCENE_ID, brightness=40, transition=2)

    assert sent_recall(client) == {
        "recall": {
            "action": "active",
            "duration": 2000,
            "dimming": {"brightness": 40.0},
        }
    }


@pytest.mark.asyncio
async def test_activate_can_start_the_scene_as_a_dynamic_palette(
    client: AsyncMock,
) -> None:
    await SceneNamespace(client).activate(SCENE_ID, dynamic=True)

    assert sent_recall(client) == {"recall": {"action": "dynamic_palette"}}
