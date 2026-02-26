from hueify.shared.exceptions import ResourceNotFoundException


class LightNotFoundException(ResourceNotFoundException):
    def __init__(
        self,
        light_name: str,
        suggestions: list[str],
        max_suggestions: int | None = None,
    ) -> None:
        super().__init__(
            resource_type="light",
            lookup_name=light_name,
            suggested_names=suggestions,
            max_suggestions=max_suggestions,
        )
