from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from hueify.http import HttpClient
from hueify.models import (
    HueApiResponse,
    Light,
    LightUpdate,
    OnState,
    ResourceIdentifier,
    ResourceType,
    SceneRecallRequest,
)
from hueify.resources import LightNamespace, SceneNamespace


@pytest.fixture
def client() -> AsyncMock:
    return AsyncMock(spec=HttpClient)


@pytest.mark.asyncio
async def test_light_list_has_concrete_response_type(client: AsyncMock) -> None:
    namespace = LightNamespace(client)
    response = HueApiResponse[Light]()
    client.get.return_value = response

    result = await namespace.list()

    assert result is response
    client.get.assert_awaited_once()
    assert client.get.await_args is not None
    assert client.get.await_args.args[0] == "light"


@pytest.mark.asyncio
async def test_light_get_addresses_resource_by_id(client: AsyncMock) -> None:
    namespace = LightNamespace(client)
    resource_id = uuid4()
    client.get.return_value = HueApiResponse[Light]()

    await namespace.get(resource_id)

    client.get.assert_awaited_once()
    assert client.get.await_args is not None
    assert client.get.await_args.args[0] == f"light/{resource_id}"


@pytest.mark.asyncio
async def test_light_update_requires_light_update_model(client: AsyncMock) -> None:
    namespace = LightNamespace(client)
    update = LightUpdate(on=OnState(on=True))
    response = HueApiResponse[ResourceIdentifier](
        data=[ResourceIdentifier(rid=uuid4(), rtype=ResourceType.LIGHT)]
    )
    client.put.return_value = response

    result = await namespace.update("light-id", update)

    assert result is response
    client.put.assert_awaited_once_with("light/light-id", update)


@pytest.mark.asyncio
async def test_scene_recall_uses_typed_default_request(client: AsyncMock) -> None:
    namespace = SceneNamespace(client)
    client.put.return_value = HueApiResponse[ResourceIdentifier]()

    await namespace.recall("scene-id")

    endpoint, request = client.put.await_args.args
    assert endpoint == "scene/scene-id"
    assert isinstance(request, SceneRecallRequest)
