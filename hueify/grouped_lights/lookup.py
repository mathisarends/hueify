from hueify.grouped_lights.exception import GroupedLightNotFoundException
from hueify.grouped_lights.models import GroupedLightInfo, GroupedLightInfoListAdapter
from hueify.http import ApiResponse
from hueify.shared.resource.lookup import ResourceLookup
from hueify.shared.resource.models import ResourceType


class GroupedLightLookup(ResourceLookup[GroupedLightInfo]):
    def get_resource_type(self) -> ResourceType:
        return ResourceType.GROUPED_LIGHT

    def _get_endpoint(self) -> str:
        return "grouped_light"

    def _parse_response(self, response: ApiResponse) -> list[GroupedLightInfo]:
        data = response.get("data", [])
        if not data:
            return []
        return GroupedLightInfoListAdapter.validate_python(data)

    def _create_not_found_exception(
        self, lookup_name: str, suggested_names: list[str]
    ) -> Exception:
        return GroupedLightNotFoundException(
            lookup_name=lookup_name, suggested_names=suggested_names
        )
