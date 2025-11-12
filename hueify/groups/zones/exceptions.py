from hueify.exceptions import ResourceNotFoundException
from hueify.groups.models import GroupType


class ZoneNotFoundException(ResourceNotFoundException):
    def __init__(self, lookup_name: str, suggested_names: list[str]) -> None:
        super().__init__(
            resource_type=GroupType.ZONE.value,
            lookup_name=lookup_name,
            suggested_names=suggested_names,
            max_suggestions=3,
        )
