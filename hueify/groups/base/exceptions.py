from hueify.types.exceptions import HueifyException


class NotInColorTemperatureModeError(HueifyException):
    def __init__(self, group_name: str) -> None:
        super().__init__(
            f"Group '{group_name}' is currently not in color temperature mode. "
            "The lights are in color mode (xy/hs). "
            "Call set_color_temperature() first to switch to CT mode."
        )
