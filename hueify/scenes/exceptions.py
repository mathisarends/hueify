from hueify.types.exceptions import HueifyException


class SceneNotFoundError(HueifyException):
    def __init__(self, lookup_name: str, suggested_names: list[str]) -> None:
        self.lookup_name = lookup_name
        self.suggested_names = suggested_names
        
        error_msg = f"Scene '{lookup_name}' not found"
        if suggested_names:
            suggestions = ", ".join([f"'{name}'" for name in suggested_names[:3]])
            error_msg += f". Did you mean: {suggestions}?"
        
        super().__init__(error_msg)