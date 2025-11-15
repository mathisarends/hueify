from hueify.groups.base.lookup import ResourceLookup
from hueify.groups.models import GroupInfo, GroupInfoListAdapter
from hueify.groups.zones.exceptions import ZoneNotFoundException
from hueify.http import ApiResponse
from hueify.shared.types import ResourceType


class ZoneLookup(ResourceLookup[GroupInfo]):
    def get_resource_type(self) -> ResourceType:
        return ResourceType.ZONE

    def _get_endpoint(self) -> str:
        return "zone"

    def _extract_name(self, entity: GroupInfo) -> str:
        return entity.name

    def _parse_response(self, response: ApiResponse) -> list[GroupInfo]:
        data = response.get("data", [])
        if not data:
            return []
        return GroupInfoListAdapter.validate_python(data)

    def _create_not_found_exception(
        self, lookup_name: str, suggested_names: list[str]
    ) -> Exception:
        return ZoneNotFoundException(
            lookup_name=lookup_name, suggested_names=suggested_names
        )
