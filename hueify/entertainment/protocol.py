from collections.abc import Iterable, Mapping
from enum import IntEnum
from uuid import UUID

from hueify.color import Color, to_rgb, xy_to_rgb
from hueify.models import ColorXY

PROTOCOL_NAME = b"HueStream"
PROTOCOL_VERSION = b"\x02\x00"

HEADER_LENGTH = 16
AREA_ID_LENGTH = 36
CHANNEL_LENGTH = 7

MAX_CHANNELS = 20

_UINT16_MAX = 0xFFFF
_UINT8_MAX = 0xFF
_SEQUENCE_MODULUS = 0x100

type Rgb = tuple[float, float, float]


class ColorSpace(IntEnum):
    RGB = 0x00
    XY_BRIGHTNESS = 0x01


BLACK: Rgb = (0.0, 0.0, 0.0)


class Frame:
    """The mutable colors of one entertainment area."""

    def __init__(self, channel_ids: Iterable[int]) -> None:
        self._colors: dict[int, Rgb] = {
            _validated_channel_id(channel_id): BLACK for channel_id in channel_ids
        }

    @property
    def channels(self) -> tuple[int, ...]:
        return tuple(self._colors)

    def __len__(self) -> int:
        return len(self._colors)

    def get(self, channel_id: int) -> Rgb:
        self._require_channel(channel_id)
        return self._colors[channel_id]

    def set(self, channel_id: int, color: Color, brightness: float = 1.0) -> None:
        self._require_channel(channel_id)
        self._colors[channel_id] = to_stream_rgb(color, brightness)

    def set_all(self, color: Color, brightness: float = 1.0) -> None:
        rgb = to_stream_rgb(color, brightness)
        self._colors = dict.fromkeys(self._colors, rgb)

    def clear(self) -> None:
        self._colors = dict.fromkeys(self._colors, BLACK)

    def colors(self) -> Mapping[int, Rgb]:
        return dict(self._colors)

    def encode(self, area_id: UUID | str, sequence: int = 0) -> bytes:
        return encode_frame(area_id, self._colors, sequence)

    def _require_channel(self, channel_id: int) -> None:
        if channel_id not in self._colors:
            known = ", ".join(str(channel) for channel in self._colors) or "none"
            raise ValueError(
                f"Channel {channel_id} is not part of this entertainment area. "
                f"Known channels: {known}"
            )


def to_stream_rgb(color: Color, brightness: float = 1.0) -> Rgb:
    if not 0.0 <= brightness <= 1.0:
        raise ValueError(f"Brightness must be between 0 and 1, got {brightness}")

    if isinstance(color, ColorXY):
        red, green, blue = xy_to_rgb(color)
    else:
        red, green, blue = to_rgb(color)

    scale = brightness / _UINT8_MAX
    return (red * scale, green * scale, blue * scale)


def encode_frame(
    area_id: UUID | str,
    colors: Mapping[int, Rgb],
    sequence: int = 0,
    color_space: ColorSpace = ColorSpace.RGB,
) -> bytes:
    if len(colors) > MAX_CHANNELS:
        raise ValueError(
            f"A frame carries at most {MAX_CHANNELS} channels, got {len(colors)}"
        )

    frame = bytearray(_encode_header(area_id, sequence, color_space))
    for channel_id, color in colors.items():
        frame.append(_validated_channel_id(channel_id))
        frame.extend(_encode_color(color))
    return bytes(frame)


def frame_length(channel_count: int) -> int:
    return HEADER_LENGTH + AREA_ID_LENGTH + CHANNEL_LENGTH * channel_count


def _encode_header(
    area_id: UUID | str, sequence: int, color_space: ColorSpace
) -> bytes:
    header = bytearray(PROTOCOL_NAME)
    header.extend(PROTOCOL_VERSION)
    header.append(sequence % _SEQUENCE_MODULUS)
    header.extend(b"\x00\x00")
    header.append(color_space)
    header.append(0x00)
    header.extend(_encode_area_id(area_id))
    return bytes(header)


def _encode_area_id(area_id: UUID | str) -> bytes:
    try:
        canonical = str(UUID(str(area_id)))
    except ValueError as error:
        raise ValueError(f"Entertainment area ID {area_id!r} is not a UUID") from error
    return canonical.encode("ascii")


def _encode_color(color: Rgb) -> bytes:
    return b"".join(_encode_channel_value(value) for value in color)


def _encode_channel_value(value: float) -> bytes:
    clamped = min(max(value, 0.0), 1.0)
    return round(clamped * _UINT16_MAX).to_bytes(2, "big")


def _validated_channel_id(channel_id: int) -> int:
    if not 0 <= channel_id <= _UINT8_MAX:
        raise ValueError(
            f"Channel ID must be between 0 and {_UINT8_MAX}, got {channel_id}"
        )
    return channel_id
