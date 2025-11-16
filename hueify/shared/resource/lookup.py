from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from hueify.http import ApiResponse, HttpClient
from hueify.shared.cache import LookupCache, get_cache
from hueify.shared.resource.models import ResourceInfo, ResourceType
from hueify.utils.fuzzy import find_all_matches_sorted

T = TypeVar("T", bound=ResourceInfo)


class ResourceLookup(ABC, Generic[T]):
    def __init__(
        self,
        client: HttpClient | None = None,
        cache: LookupCache | None = None,
    ) -> None:
        self._client = client or HttpClient()
        self._cache = cache or get_cache()

    async def get_entity_by_name(self, entity_name: str) -> T:
        entities = await self.get_all_entities()

        for entity in entities:
            if entity.metadata.name.lower() == entity_name.lower():
                return entity

        matching_entities = find_all_matches_sorted(
            query=entity_name,
            items=entities,
            text_extractor=lambda e: e.metadata.name,
        )

        suggestions = [entity.metadata.name for entity in matching_entities]

        raise self._create_not_found_exception(
            lookup_name=entity_name, suggested_names=suggestions
        )

    async def get_all_entities(self) -> list[T]:
        resource_type = self.get_resource_type()
        return await self._cache.get_or_fetch(
            entity_type=resource_type,
            all_entities_fetcher=self._fetch_all_entities,
        )

    async def _fetch_all_entities(self) -> list[T]:
        response = await self._client.get(self._get_endpoint())
        return self._parse_response(response)

    @abstractmethod
    def get_resource_type(self) -> ResourceType:
        pass

    @abstractmethod
    def _get_endpoint(self) -> str:
        pass

    @abstractmethod
    def _parse_response(self, response: ApiResponse) -> list[T]:
        pass

    @abstractmethod
    def _create_not_found_exception(
        self, lookup_name: str, suggested_names: list[str]
    ) -> Exception:
        pass
