from unittest.mock import AsyncMock

import pytest
from pydantic import BaseModel

from hueify.shared.cache.lookup import LookupCache, get_cache
from hueify.shared.types import ResourceType


class TestResource(BaseModel):
    id: str
    name: str


@pytest.fixture
def fresh_cache() -> LookupCache:
    return LookupCache()


@pytest.mark.asyncio
async def test_cache_returns_fresh_data_on_miss(
    fresh_cache: LookupCache,
) -> None:
    fetcher = AsyncMock(return_value=[TestResource(id="1", name="Test")])

    result = await fresh_cache.get_or_fetch(ResourceType.LIGHT, fetcher)

    assert len(result) == 1
    assert result[0].id == "1"
    fetcher.assert_called_once()


@pytest.mark.asyncio
async def test_cache_returns_cached_data_on_hit(
    fresh_cache: LookupCache,
) -> None:
    fetcher = AsyncMock(return_value=[TestResource(id="1", name="Test")])

    await fresh_cache.get_or_fetch(ResourceType.LIGHT, fetcher)
    result = await fresh_cache.get_or_fetch(ResourceType.LIGHT, fetcher)

    assert len(result) == 1
    assert result[0].id == "1"
    fetcher.assert_called_once()


@pytest.mark.asyncio
async def test_cache_calls_fetcher_only_once_with_concurrent_requests(
    fresh_cache: LookupCache,
) -> None:
    import asyncio

    fetcher = AsyncMock(return_value=[TestResource(id="1", name="Test")])

    results = await asyncio.gather(
        fresh_cache.get_or_fetch(ResourceType.LIGHT, fetcher),
        fresh_cache.get_or_fetch(ResourceType.LIGHT, fetcher),
        fresh_cache.get_or_fetch(ResourceType.LIGHT, fetcher),
    )

    assert all(len(r) == 1 for r in results)
    fetcher.assert_called_once()


@pytest.mark.asyncio
async def test_cache_stores_different_resource_types_separately(
    fresh_cache: LookupCache,
) -> None:
    light_fetcher = AsyncMock(return_value=[TestResource(id="light-1", name="Light")])
    scene_fetcher = AsyncMock(return_value=[TestResource(id="scene-1", name="Scene")])

    light_result = await fresh_cache.get_or_fetch(ResourceType.LIGHT, light_fetcher)
    scene_result = await fresh_cache.get_or_fetch(ResourceType.SCENE, scene_fetcher)

    assert light_result[0].id == "light-1"
    assert scene_result[0].id == "scene-1"
    light_fetcher.assert_called_once()
    scene_fetcher.assert_called_once()


@pytest.mark.asyncio
async def test_clear_all_empties_cache(fresh_cache: LookupCache) -> None:
    fetcher = AsyncMock(return_value=[TestResource(id="1", name="Test")])

    await fresh_cache.get_or_fetch(ResourceType.LIGHT, fetcher)
    await fresh_cache.clear_all()
    await fresh_cache.get_or_fetch(ResourceType.LIGHT, fetcher)

    assert fetcher.call_count == 2


@pytest.mark.asyncio
async def test_clear_by_type_removes_specific_resource_type(
    fresh_cache: LookupCache,
) -> None:
    light_fetcher = AsyncMock(return_value=[TestResource(id="light-1", name="Light")])
    scene_fetcher = AsyncMock(return_value=[TestResource(id="scene-1", name="Scene")])

    await fresh_cache.get_or_fetch(ResourceType.LIGHT, light_fetcher)
    await fresh_cache.get_or_fetch(ResourceType.SCENE, scene_fetcher)
    await fresh_cache.clear_by_type(ResourceType.LIGHT)

    await fresh_cache.get_or_fetch(ResourceType.LIGHT, light_fetcher)
    await fresh_cache.get_or_fetch(ResourceType.SCENE, scene_fetcher)

    assert light_fetcher.call_count == 2
    assert scene_fetcher.call_count == 1


@pytest.mark.asyncio
async def test_clear_by_type_nonexistent_type_does_not_raise(
    fresh_cache: LookupCache,
) -> None:
    await fresh_cache.clear_by_type(ResourceType.LIGHT)


@pytest.mark.asyncio
async def test_get_cache_returns_same_instance() -> None:
    cache1 = get_cache()
    cache2 = get_cache()

    assert cache1 is cache2


@pytest.mark.asyncio
async def test_get_cache_singleton_pattern() -> None:
    cache = get_cache()
    fetcher = AsyncMock(return_value=[TestResource(id="1", name="Test")])

    await cache.get_or_fetch(ResourceType.LIGHT, fetcher)

    cache2 = get_cache()
    result = await cache2.get_or_fetch(ResourceType.LIGHT, fetcher)

    assert len(result) == 1
    fetcher.assert_called_once()
