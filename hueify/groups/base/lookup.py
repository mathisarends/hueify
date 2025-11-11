from abc import ABC, abstractmethod

from hueify.groups.models import GroupInfo, GroupInfoListAdapter
from hueify.http import HttpClient, ApiResponse
from hueify.utils.fuzzy import find_all_matches

class GroupLookup(ABC):
    def __init__(self, client: HttpClient | None = None) -> None:
        self._client = client or HttpClient()

    async def get_group_by_name(self, group_name: str) -> GroupInfo:
        groups = await self._get_all_groups()
        
        for group in groups:
            if group.name.lower() == group_name.lower():
                return group
        
        suggestions = find_all_matches(
            query=group_name,
            items=groups,
            text_extractor=lambda g: g.name,
            min_similarity=0.6
        )

        raise self._create_not_found_exception(
            lookup_name=group_name,
            suggested_names=[s.name for s in suggestions]
        )
    
    async def _get_all_groups(self) -> list[GroupInfo]:
        response = await self._client.get(self._get_endpoint())
        return self._parse_groups_response(response)
    
    @abstractmethod
    def _get_endpoint(self) -> str:
        pass

    @abstractmethod
    def _create_not_found_exception(
        self, 
        lookup_name: str, 
        suggested_names: list[str]
    ) -> Exception:
        pass

    def _parse_groups_response(self, response: ApiResponse) -> list[GroupInfo]:
        data = response.get("data", [])
        if not data:
            return []
        
        return GroupInfoListAdapter.validate_python(data)
