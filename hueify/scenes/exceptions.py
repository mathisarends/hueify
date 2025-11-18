from hueify.shared.exceptions import ResourceNotFoundException


class SceneNotFoundException(ResourceNotFoundException):
    def __init__(
        self,
        lookup_name: str,
        suggested_names: list[str],
        max_suggestions: int | None = None,
    ) -> None:
        super().__init__(
            resource_type="scene",
            lookup_name=lookup_name,
            suggested_names=suggested_names,
            max_suggestions=max_suggestions,
        )


class NoActiveSceneException(Exception):
    def __init__(
        self, group_name: str, is_light_on: bool, brightness: float | None = None
    ) -> None:
        self._group_name = group_name
        self._is_light_on = is_light_on
        self._brightness = brightness

        if not is_light_on:
            message = f"No active scene found in group '{group_name}' (lights are OFF)"
        elif brightness is not None:
            message = f"No active scene found in group '{group_name}' (lights are ON at {brightness:.1f}% _brightness)"
        else:
            message = f"No active scene found in group '{group_name}' (lights are ON)"

        super().__init__(message)
