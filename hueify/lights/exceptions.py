from hueify.exceptions import ResourceNotFoundException


class LightNotFoundError(ResourceNotFoundException):
    def __init__(self, light_name: str, suggestions: list[str]) -> None:
        super().__init__(
            resource_type="light",
            lookup_name=light_name,
            suggested_names=suggestions,
            max_suggestions=5,
        )
