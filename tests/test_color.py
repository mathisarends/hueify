import pytest

from hueify.color import (
    kelvin_to_mirek,
    mirek_to_kelvin,
    rgb_to_xy,
    to_rgb,
    to_xy,
    xy_to_hex,
    xy_to_rgb,
)
from hueify.models import ColorXY


def test_hex_shorthand_and_longhand_resolve_to_the_same_rgb() -> None:
    assert to_rgb("#f80") == to_rgb("ff8800") == (255, 136, 0)


def test_named_colors_are_case_and_separator_insensitive() -> None:
    assert to_rgb("Warm White") == to_rgb("warm_white") == to_rgb("warm-white")


def test_unknown_color_names_report_the_accepted_formats() -> None:
    with pytest.raises(ValueError, match="Unknown color"):
        to_rgb("chartreuse-ish")


def test_pure_red_maps_into_the_red_corner_of_the_gamut() -> None:
    xy = rgb_to_xy((255, 0, 0))

    assert xy.x == pytest.approx(0.735, abs=0.01)
    assert xy.y == pytest.approx(0.265, abs=0.01)
    assert xy.x > rgb_to_xy((0, 255, 0)).x
    assert xy.y < rgb_to_xy((0, 255, 0)).y


def test_xy_roundtrip_preserves_the_perceived_hue() -> None:
    red, green, blue = xy_to_rgb(to_xy("#ff8800"))

    assert red > green > blue


def test_already_typed_color_is_passed_through_unchanged() -> None:
    xy = ColorXY(x=0.3, y=0.4)

    assert to_xy(xy) is xy


def test_black_has_no_chromaticity() -> None:
    assert rgb_to_xy((0, 0, 0)) == ColorXY(x=0.0, y=0.0)


def test_xy_to_rgb_scales_with_brightness() -> None:
    xy = to_xy("#ffffff")

    assert max(xy_to_rgb(xy, brightness=100)) > max(xy_to_rgb(xy, brightness=20))


def test_xy_renders_back_to_a_hex_string() -> None:
    rendered = xy_to_hex(to_xy("#ffffff"))

    assert rendered.startswith("#")
    assert min(to_rgb(rendered)) > 230


def test_kelvin_is_clamped_to_the_range_hue_lamps_accept() -> None:
    assert kelvin_to_mirek(2700) == 370
    assert kelvin_to_mirek(1000) == 500
    assert kelvin_to_mirek(10000) == 153


def test_mirek_converts_back_to_kelvin() -> None:
    assert mirek_to_kelvin(370) == 2703


def test_non_positive_color_temperatures_are_rejected() -> None:
    with pytest.raises(ValueError, match="must be positive"):
        kelvin_to_mirek(0)
