from hueify.groups.models import GroupInfo
from hueify.groups.zones.exceptions import ZoneNotFoundException
from hueify.shared.resource.lookup import NamedResourceLookup


class ZoneLookup(NamedResourceLookup[GroupInfo]):
    def get_model_type(self) -> type[GroupInfo]:
        return GroupInfo

    def _get_endpoint(self) -> str:
        return "zone"

    def _create_not_found_exception(
        self, lookup_name: str, suggested_names: list[str]
    ) -> Exception:
        return ZoneNotFoundException(
            lookup_name=lookup_name, suggested_names=suggested_names
        )
