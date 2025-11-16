from hueify.shared.exceptions import ResourceNotFoundException
from hueify.shared.types.groups import GroupType


class ZoneNotFoundException(ResourceNotFoundException):
    def __init__(
        self,
        lookup_name: str,
        suggested_names: list[str],
        max_suggestions: int | None = None,
    ) -> None:
        super().__init__(
            resource_type=GroupType.ZONE,
            lookup_name=lookup_name,
            suggested_names=suggested_names,
            max_suggestions=max_suggestions,
        )
