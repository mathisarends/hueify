class HueifyException(Exception):
    """Base exception for all Hueify errors."""


class ResourceNotFoundException(HueifyException):
    """Raised when a named resource (light, room, zone, scene) cannot be found.

    The message includes fuzzy suggestions from the available names to help
    callers surface actionable feedback.
    """

    def __init__(
        self,
        resource_type: str,
        lookup_name: str,
        suggested_names: list[str],
        max_suggestions: int | None = None,
    ) -> None:
        """
        Args:
            resource_type: Human-readable resource kind, e.g. ``"light"`` or ``"room"``.
            lookup_name: The name that was requested but not found.
            suggested_names: All available names used to build the "Did you mean …?" hint.
            max_suggestions: Caps how many suggestions appear in the message.
        """
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
