"""Conversions between developer-friendly colors and the Hue CIE xy space."""

from hueify.models import ColorXY

type RGB = tuple[int, int, int]
type Color = str | RGB | ColorXY

MIREK_MINIMUM = 153
MIREK_MAXIMUM = 500

NAMED_COLORS: dict[str, RGB] = {
    "black": (0, 0, 0),
    "white": (255, 255, 255),
    "red": (255, 0, 0),
    "green": (0, 255, 0),
    "blue": (0, 0, 255),
    "yellow": (255, 255, 0),
    "cyan": (0, 255, 255),
    "magenta": (255, 0, 255),
    "orange": (255, 165, 0),
    "pink": (255, 105, 180),
    "purple": (128, 0, 128),
    "violet": (138, 43, 226),
    "turquoise": (64, 224, 208),
    "lime": (50, 205, 50),
    "gold": (255, 215, 0),
    "warm_white": (255, 180, 107),
    "cool_white": (212, 235, 255),
}


def to_xy(color: Color) -> ColorXY:
    if isinstance(color, ColorXY):
        return color
    return rgb_to_xy(to_rgb(color))


def to_rgb(color: str | RGB) -> RGB:
    if isinstance(color, str):
        return _parse_color_name(color)
    return _validated_rgb(color)


def rgb_to_xy(rgb: RGB) -> ColorXY:
    red, green, blue = (_gamma_expand(channel / 255) for channel in _validated_rgb(rgb))

    x = red * 0.649926 + green * 0.103455 + blue * 0.197109
    y = red * 0.234327 + green * 0.743075 + blue * 0.022598
    z = green * 0.053077 + blue * 1.035763

    total = x + y + z
    if total == 0:
        return ColorXY(x=0.0, y=0.0)
    return ColorXY(x=round(x / total, 4), y=round(y / total, 4))


def xy_to_rgb(xy: ColorXY, brightness: float = 100.0) -> RGB:
    if xy.y == 0:
        return (0, 0, 0)

    luminance = max(0.0, min(brightness, 100.0)) / 100
    x = (luminance / xy.y) * xy.x
    z = (luminance / xy.y) * (1 - xy.x - xy.y)

    red = x * 1.656492 - luminance * 0.354851 - z * 0.255038
    green = -x * 0.707196 + luminance * 1.655397 + z * 0.036152
    blue = x * 0.051713 - luminance * 0.121364 + z * 1.011530

    channels = [_gamma_compress(channel) for channel in (red, green, blue)]
    peak = max(channels)
    if peak > 1:
        channels = [channel / peak for channel in channels]

    red_out, green_out, blue_out = (
        round(max(0.0, min(channel, 1.0)) * 255) for channel in channels
    )
    return (red_out, green_out, blue_out)


def xy_to_hex(xy: ColorXY, brightness: float = 100.0) -> str:
    red, green, blue = xy_to_rgb(xy, brightness)
    return f"#{red:02x}{green:02x}{blue:02x}"


def kelvin_to_mirek(kelvin: int) -> int:
    if kelvin <= 0:
        raise ValueError("Color temperature in kelvin must be positive")
    return _clamp_mirek(round(1_000_000 / kelvin))


def mirek_to_kelvin(mirek: int) -> int:
    if mirek <= 0:
        raise ValueError("Color temperature in mirek must be positive")
    return round(1_000_000 / mirek)


def _clamp_mirek(mirek: int) -> int:
    return max(MIREK_MINIMUM, min(mirek, MIREK_MAXIMUM))


def hex_to_rgb(hex_color: str) -> RGB:
    value = hex_color.strip().lstrip("#")
    if len(value) == 3:
        value = "".join(channel * 2 for channel in value)
    if len(value) != 6:
        raise ValueError(
            f"Invalid hex color {hex_color!r}: expected '#rgb' or '#rrggbb'"
        )
    try:
        return (int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16))
    except ValueError as error:
        raise ValueError(f"Invalid hex color {hex_color!r}") from error


def _parse_color_name(color: str) -> RGB:
    normalized = color.strip().lower().replace(" ", "_").replace("-", "_")
    if named := NAMED_COLORS.get(normalized):
        return named
    try:
        return hex_to_rgb(color)
    except ValueError as error:
        if color.strip().startswith("#"):
            raise
        raise ValueError(
            f"Unknown color {color!r}: expected a hex string like '#ff8800', "
            f"an (r, g, b) tuple or one of {', '.join(sorted(NAMED_COLORS))}"
        ) from error


def _validated_rgb(rgb: RGB) -> RGB:
    if len(rgb) != 3 or any(not 0 <= channel <= 255 for channel in rgb):
        raise ValueError(f"Invalid RGB color {rgb!r}: expected three values in 0-255")
    return rgb


def _gamma_expand(channel: float) -> float:
    if channel > 0.04045:
        return ((channel + 0.055) / 1.055) ** 2.4
    return channel / 12.92


def _gamma_compress(channel: float) -> float:
    if channel <= 0.0031308:
        return 12.92 * channel
    return 1.055 * (max(channel, 0.0) ** (1 / 2.4)) - 0.055
