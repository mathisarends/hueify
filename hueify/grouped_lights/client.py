from uuid import UUID

from hueify.grouped_lights.exception import GroupedLightNotFoundException
from hueify.grouped_lights.models import GroupedLightInfo, GroupedLightInfoListAdapter
from hueify.http import ApiResponse, HttpClient
from hueify.shared.cache import get_cache
from hueify.shared.resource.models import ResourceType


class GroupedLightClient:
    def __init__(self, client: HttpClient | None = None) -> None:
        self._client = client or HttpClient()
        self._cache = get_cache()

    async def get_by_id(self, grouped_light_id: UUID) -> GroupedLightInfo:
        cached = self._cache.get_by_id(ResourceType.GROUPED_LIGHT, grouped_light_id)
        if cached:
            return cached

        await self._ensure_cache_populated()

        cached = self._cache.get_by_id(ResourceType.GROUPED_LIGHT, grouped_light_id)
        if cached:
            return cached

        raise GroupedLightNotFoundException(
            lookup_name=str(grouped_light_id),
            suggested_names=[],
        )

    async def get_all(self) -> list[GroupedLightInfo]:
        cached = self._cache.get_by_id(ResourceType.GROUPED_LIGHT, None)
        if cached:
            return self._cache._grouped_lights_cache.get_all()

        return await self._fetch_and_cache_all()

    async def _ensure_cache_populated(self) -> None:
        cached_items = self._cache._grouped_lights_cache.get_all()
        if not cached_items:
            await self._fetch_and_cache_all()

    async def _fetch_and_cache_all(self) -> list[GroupedLightInfo]:
        response = await self._client.get("grouped_light")
        grouped_lights = self._parse_response(response)
        await self._cache._grouped_lights_cache.store_all(grouped_lights)
        return grouped_lights

    def _parse_response(self, response: ApiResponse) -> list[GroupedLightInfo]:
        data = response.get("data", [])
        if not data:
            return []
        return GroupedLightInfoListAdapter.validate_python(data)
