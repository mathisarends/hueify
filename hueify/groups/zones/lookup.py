from hueify.groups.base import GroupLookup
from hueify.groups.zones.exceptions import ZoneNotFoundExeption


class ZoneLookup(GroupLookup):
    def _get_endpoint(self) -> str:
        return "zone"

    def _create_not_found_exception(
        self, 
        lookup_name: str, 
        suggested_names: list[str]
    ) -> Exception:
        return ZoneNotFoundExeption(
            lookup_name=lookup_name,
            suggested_names=suggested_names
        )
