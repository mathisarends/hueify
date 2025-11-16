from hueify.shared.exceptions import ResourceNotFoundException
from hueify.shared.resource.models import ResourceType


class GroupedLightNotFoundException(ResourceNotFoundException):
    def __init__(
        self,
        lookup_name: str,
        suggested_names: list[str],
        max_suggestions: int | None = None,
    ) -> None:
        super().__init__(
            resource_type=ResourceType.GROUPED_LIGHT,
            lookup_name=lookup_name,
            suggested_names=suggested_names,
            max_suggestions=max_suggestions,
        )
