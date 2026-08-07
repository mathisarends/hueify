from uuid import UUID

import pytest

from hueify.entertainment.protocol import (
    AREA_ID_LENGTH,
    CHANNEL_LENGTH,
    HEADER_LENGTH,
    MAX_CHANNELS,
    ColorSpace,
    Frame,
    encode_frame,
    frame_length,
    to_stream_rgb,
)
from hueify.models import ColorXY

AREA_ID = UUID("a1b2c3d4-1111-2222-3333-444455556666")

WHITE = (1.0, 1.0, 1.0)
BLACK = (0.0, 0.0, 0.0)


def header(frame: bytes) -> bytes:
    return frame[:HEADER_LENGTH]


def area_id_of(frame: bytes) -> str:
    return frame[HEADER_LENGTH : HEADER_LENGTH + AREA_ID_LENGTH].decode("ascii")


def channels_of(frame: bytes) -> bytes:
    return frame[HEADER_LENGTH + AREA_ID_LENGTH :]


class TestEncodeFrame:
    def test_writes_the_documented_layout(self) -> None:
        frame = encode_frame(AREA_ID, {0: WHITE, 3: BLACK}, sequence=7)

        assert header(frame) == (
            b"HueStream"  # protocol name
            b"\x02\x00"  # version 2.0
            b"\x07"  # sequence
            b"\x00\x00"  # reserved
            b"\x00"  # color space: RGB
            b"\x00"  # reserved
        )
        assert area_id_of(frame) == str(AREA_ID)
        assert channels_of(frame) == (
            b"\x00\xff\xff\xff\xff\xff\xff"  # channel 0, full white
            b"\x03\x00\x00\x00\x00\x00\x00"  # channel 3, black
        )

    def test_length_is_the_header_plus_seven_bytes_per_channel(self) -> None:
        frame = encode_frame(AREA_ID, dict.fromkeys(range(5), WHITE))

        assert len(frame) == frame_length(5)
        assert len(frame) == HEADER_LENGTH + AREA_ID_LENGTH + 5 * CHANNEL_LENGTH

    def test_keeps_the_channel_order_it_was_given(self) -> None:
        frame = encode_frame(AREA_ID, {4: BLACK, 1: BLACK, 2: BLACK})

        assert channels_of(frame)[::CHANNEL_LENGTH] == bytes([4, 1, 2])

    def test_sequence_wraps_into_its_single_byte(self) -> None:
        assert header(encode_frame(AREA_ID, {}, sequence=256))[11] == 0
        assert header(encode_frame(AREA_ID, {}, sequence=257))[11] == 1

    def test_color_space_is_announced_in_the_header(self) -> None:
        frame = encode_frame(AREA_ID, {}, color_space=ColorSpace.XY_BRIGHTNESS)

        assert header(frame)[14] == ColorSpace.XY_BRIGHTNESS

    def test_channel_values_are_big_endian_and_clamped(self) -> None:
        frame = encode_frame(AREA_ID, {0: (0.5, 2.0, -1.0)})

        assert channels_of(frame) == b"\x00\x80\x00\xff\xff\x00\x00"

    def test_area_id_must_be_a_uuid(self) -> None:
        with pytest.raises(ValueError, match="not a UUID"):
            encode_frame("the-tv-area", {0: WHITE})

    def test_accepts_the_area_id_as_a_string(self) -> None:
        assert encode_frame(str(AREA_ID), {}) == encode_frame(AREA_ID, {})

    def test_refuses_more_channels_than_an_area_can_hold(self) -> None:
        colors = dict.fromkeys(range(MAX_CHANNELS + 1), WHITE)

        with pytest.raises(ValueError, match=f"at most {MAX_CHANNELS} channels"):
            encode_frame(AREA_ID, colors)

    def test_refuses_a_channel_id_that_does_not_fit_its_byte(self) -> None:
        with pytest.raises(ValueError, match="between 0 and 255"):
            encode_frame(AREA_ID, {256: WHITE})


class TestStreamColors:
    def test_reads_hex_and_named_colors_like_the_rest_of_hueify(self) -> None:
        assert to_stream_rgb("#ff8800") == pytest.approx((1.0, 136 / 255, 0.0))
        assert to_stream_rgb("red") == (1.0, 0.0, 0.0)
        assert to_stream_rgb((0, 128, 255)) == pytest.approx((0.0, 128 / 255, 1.0))

    def test_reads_cie_xy_by_converting_it(self) -> None:
        red = to_stream_rgb(ColorXY(x=0.675, y=0.322))

        assert red[0] > red[1] and red[0] > red[2]

    def test_brightness_scales_every_channel(self) -> None:
        assert to_stream_rgb("white", brightness=0.5) == (0.5, 0.5, 0.5)
        assert to_stream_rgb("white", brightness=0.0) == BLACK

    def test_brightness_outside_zero_to_one_is_refused(self) -> None:
        with pytest.raises(ValueError, match="between 0 and 1"):
            to_stream_rgb("white", brightness=1.5)

    def test_an_eight_bit_channel_fills_its_sixteen_bits(self) -> None:
        frame = encode_frame(AREA_ID, {0: to_stream_rgb((255, 136, 0))})

        assert channels_of(frame) == b"\x00\xff\xff\x88\x88\x00\x00"


class TestFrame:
    def test_starts_black_on_every_channel_of_the_area(self) -> None:
        frame = Frame([0, 1])

        assert frame.channels == (0, 1)
        assert len(frame) == 2
        assert frame.get(0) == BLACK

    def test_set_all_replaces_every_channel(self) -> None:
        frame = Frame([0, 1])

        frame.set_all("white")

        assert frame.colors() == {0: WHITE, 1: WHITE}

    def test_set_touches_one_channel_only(self) -> None:
        frame = Frame([0, 1])

        frame.set(1, "white")

        assert frame.get(0) == BLACK
        assert frame.get(1) == WHITE

    def test_clear_turns_everything_black_again(self) -> None:
        frame = Frame([0])
        frame.set_all("white")

        frame.clear()

        assert frame.get(0) == BLACK

    def test_a_channel_outside_the_area_is_named_in_the_error(self) -> None:
        frame = Frame([0, 4])

        with pytest.raises(ValueError, match="Known channels: 0, 4"):
            frame.set(2, "white")

    def test_colors_snapshot_does_not_follow_later_writes(self) -> None:
        frame = Frame([0])
        snapshot = frame.colors()

        frame.set_all("white")

        assert snapshot == {0: BLACK}

    def test_encodes_itself_for_one_area(self) -> None:
        frame = Frame([0])
        frame.set_all("white")

        assert frame.encode(AREA_ID, 2) == encode_frame(AREA_ID, {0: WHITE}, 2)
