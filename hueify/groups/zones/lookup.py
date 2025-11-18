from typing import override

from hueify.groups.models import GroupInfo
from hueify.groups.zones.exceptions import ZoneNotFoundException
from hueify.shared.resource.lookup import NamedResourceLookup
from hueify.shared.resource.models import ResourceType


class ZoneLookup(NamedResourceLookup[GroupInfo]):
    @override
    def get_resource_type(self) -> ResourceType:
        return ResourceType.ZONE

    @override
    def get_model_type(self) -> type[GroupInfo]:
        return GroupInfo

    @override
    def _get_endpoint(self) -> str:
        return "zone"

    @override
    def _create_not_found_exception(
        self, lookup_name: str, suggested_names: list[str]
    ) -> Exception:
        return ZoneNotFoundException(
            lookup_name=lookup_name, suggested_names=suggested_names
        )
