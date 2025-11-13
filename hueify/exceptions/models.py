class HueifyException(Exception):
    pass


class ResourceNotFoundException(HueifyException):
    def __init__(
        self,
        resource_type: str,
        lookup_name: str,
        suggested_names: list[str],
        max_suggestions: int | None = None,
    ) -> None:
        self.resource_type = resource_type
        self.lookup_name = lookup_name
        self.suggested_names = suggested_names

        error_msg = f"{resource_type.capitalize()} '{lookup_name}' not found"
        if suggested_names:
            limited_suggestions = (
                suggested_names[:max_suggestions]
                if max_suggestions
                else suggested_names
            )
            suggestions = ", ".join([f"'{name}'" for name in limited_suggestions])
            error_msg += f". Did you mean: {suggestions}?"

        super().__init__(error_msg)
