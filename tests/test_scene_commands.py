from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from hueify.http import HttpClient
from hueify.models import (
    HueApiResponse,
    ResourceIdentifier,
    SceneMetadata,
    SceneRecallRequest,
    SceneUpdate,
)
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


@pytest.mark.asyncio
async def test_create_posts_to_the_scene_collection_endpoint(
    client: AsyncMock,
) -> None:
    update = SceneUpdate(metadata=SceneMetadata(name="Focus"))

    await SceneNamespace(client).create(update)

    endpoint, data = client.post.await_args.args
    assert endpoint == "scene"
    assert data is update


@pytest.mark.asyncio
async def test_update_puts_to_the_specific_scene_endpoint(client: AsyncMock) -> None:
    update = SceneUpdate(metadata=SceneMetadata(name="Focus"))

    await SceneNamespace(client).update(SCENE_ID, update)

    endpoint, data = client.put.await_args.args
    assert endpoint == f"scene/{SCENE_ID}"
    assert data is update


@pytest.mark.asyncio
async def test_delete_removes_the_specific_scene_endpoint(client: AsyncMock) -> None:
    await SceneNamespace(client).delete(SCENE_ID)

    client.delete.assert_awaited_once_with(f"scene/{SCENE_ID}")


@pytest.mark.asyncio
async def test_same_scene_name_can_be_scoped_to_a_group(client):
    from hueify import AmbiguousResourceError, ResourceNotFoundError
    from hueify.models import Scene

    groups = [
        "11111111-1111-1111-1111-111111111111",
        "22222222-2222-2222-2222-222222222222",
    ]
    client.get.return_value = HueApiResponse[Scene].model_validate(
        {
            "data": [
                {
                    "id": str(SCENE_ID),
                    "metadata": {"name": "Relax"},
                    "group": {"rid": groups[0], "rtype": "room"},
                },
                {
                    "id": "99999999-9999-9999-9999-999999999999",
                    "metadata": {"name": "Relax"},
                    "group": {"rid": groups[1], "rtype": "zone"},
                },
            ]
        }
    )
    scenes = SceneNamespace(client)
    with pytest.raises(AmbiguousResourceError):
        await scenes.find_by_name("Relax")
    assert (
        await scenes.find_by_name("Relax", group_id=groups[0], fuzzy=False)
    ).id == SCENE_ID
    with pytest.raises(ResourceNotFoundError):
        await scenes.find_by_name(
            "Relax", group_id="33333333-3333-3333-3333-333333333333"
        )


@pytest.mark.asyncio
@pytest.mark.parametrize("representation", ["uuid", "canonical", "uppercase", "hex"])
async def test_scene_group_filter_normalizes_uuid_representations(
    client, representation
):
    from hueify.models import Scene

    group_id = UUID("abcdefab-1234-4234-8234-abcdefabcdef")
    representations = {
        "uuid": group_id,
        "canonical": str(group_id),
        "uppercase": str(group_id).upper(),
        "hex": group_id.hex,
    }
    client.get.return_value = HueApiResponse[Scene].model_validate(
        {
            "data": [
                {
                    "id": str(SCENE_ID),
                    "metadata": {"name": "Relax"},
                    "group": {"rid": str(group_id), "rtype": "room"},
                }
            ]
        }
    )
    scene = await SceneNamespace(client).find_by_name(
        "Relax", group_id=representations[representation]
    )
    assert scene.id == SCENE_ID


@pytest.mark.asyncio
async def test_invalid_scene_group_id_fails_before_reading_the_bridge(client):
    with pytest.raises(ValueError):
        await SceneNamespace(client).find_by_name("Relax", group_id="not-a-uuid")
    client.get.assert_not_awaited()
