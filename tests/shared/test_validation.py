from hueify.shared.validation import (
    clamp_brightness,
    clamp_temperature_percentage,
    mirek_to_percentage,
    percentage_to_mirek,
)


class TestClampBrightness:
    def test_clamps_negative_brightness_to_zero(self) -> None:
        assert clamp_brightness(-10) == 0

    def test_clamps_brightness_above_hundred(self) -> None:
        assert clamp_brightness(150) == 100

    def test_returns_brightness_within_range(self) -> None:
        assert clamp_brightness(50) == 50

    def test_clamps_zero(self) -> None:
        assert clamp_brightness(0) == 0

    def test_clamps_hundred(self) -> None:
        assert clamp_brightness(100) == 100


class TestClampTemperaturePercentage:
    def test_clamps_negative_temperature_to_zero(self) -> None:
        assert clamp_temperature_percentage(-10) == 0

    def test_clamps_temperature_above_hundred(self) -> None:
        assert clamp_temperature_percentage(150) == 100

    def test_returns_temperature_within_range(self) -> None:
        assert clamp_temperature_percentage(50) == 50


class TestPercentageToMirek:
    def test_converts_zero_percent_to_minimum_mirek(self) -> None:
        assert percentage_to_mirek(0) == 153

    def test_converts_hundred_percent_to_maximum_mirek(self) -> None:
        assert percentage_to_mirek(100) == 500

    def test_converts_fifty_percent_to_middle_mirek(self) -> None:
        expected = int(153 + (50 / 100) * (500 - 153))
        assert percentage_to_mirek(50) == expected


class TestMirekToPercentage:
    def test_converts_minimum_mirek_to_zero_percent(self) -> None:
        assert mirek_to_percentage(153) == 0

    def test_converts_maximum_mirek_to_hundred_percent(self) -> None:
        assert mirek_to_percentage(500) == 100

    def test_converts_middle_mirek_to_fifty_percent(self) -> None:
        middle_mirek = int(153 + (500 - 153) / 2)
        result = mirek_to_percentage(middle_mirek)
        assert 49 <= result <= 51
