from abc import ABC, abstractmethod

from hueify.groups.models import GroupInfo, GroupInfoListAdapter
from hueify.http import ApiResponse, HttpClient
from hueify.utils.fuzzy import find_all_matches_sorted


class GroupLookup(ABC):
    def __init__(self, client: HttpClient | None = None) -> None:
        self._client = client or HttpClient()

    async def get_entity_by_name(self, group_name: str) -> GroupInfo:
        groups = await self.get_all_entities()

        for group in groups:
            if group.name.lower() == group_name.lower():
                return group

        matching_groups = find_all_matches_sorted(
            query=group_name,
            items=groups,
            text_extractor=lambda g: g.name,
        )

        suggestions = [group.name for group in matching_groups]

        raise self._create_not_found_exception(
            lookup_name=group_name, suggested_names=suggestions
        )

    async def get_all_entities(self) -> list[GroupInfo]:
        response = await self._client.get(self._get_endpoint())
        return self._parse_groups_response(response)

    @abstractmethod
    def _get_endpoint(self) -> str:
        pass

    @abstractmethod
    def _create_not_found_exception(
        self, lookup_name: str, suggested_names: list[str]
    ) -> Exception:
        pass

    # TODO: This could be used with resource fetch
    def _parse_groups_response(self, response: ApiResponse) -> list[GroupInfo]:
        data = response.get("data", [])
        if not data:
            return []

        return GroupInfoListAdapter.validate_python(data)
