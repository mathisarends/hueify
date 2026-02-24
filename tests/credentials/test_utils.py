import pytest
from hueify.credentials.service import validate_hue_app_key, validate_hue_bridge_ip


class TestValidateHueAppKey:
    def test_returns_none_when_value_is_none(self) -> None:
        assert validate_hue_app_key(None) is None

    def test_accepts_valid_app_key(self) -> None:
        valid_key = "a" * 40
        assert validate_hue_app_key(valid_key) == valid_key

    def test_rejects_app_key_below_minimum_length(self) -> None:
        short_key = "abc123"
        with pytest.raises(ValueError, match="must be at least 20 characters"):
            validate_hue_app_key(short_key)

    def test_rejects_app_key_with_special_characters(self) -> None:
        invalid_key = "a" * 19 + "!"
        with pytest.raises(ValueError, match="alphanumeric"):
            validate_hue_app_key(invalid_key)

    def test_rejects_app_key_with_spaces(self) -> None:
        invalid_key = "a" * 19 + " "
        with pytest.raises(ValueError, match="alphanumeric"):
            validate_hue_app_key(invalid_key)

    def test_accepts_exactly_minimum_length(self) -> None:
        key_at_minimum = "a" * 20
        assert validate_hue_app_key(key_at_minimum) == key_at_minimum

    def test_accepts_mixed_alphanumeric(self) -> None:
        mixed_key = "abc123def456ghi789jkl"
        assert validate_hue_app_key(mixed_key) == mixed_key


class TestValidateHueBridgeIp:
    def test_returns_none_when_value_is_none(self) -> None:
        assert validate_hue_bridge_ip(None) is None

    def test_accepts_valid_ip_address(self) -> None:
        valid_ip = "192.168.1.1"
        assert validate_hue_bridge_ip(valid_ip) == valid_ip

    def test_rejects_empty_string(self) -> None:
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_hue_bridge_ip("")

    def test_rejects_ip_with_leading_whitespace(self) -> None:
        invalid_ip = " 192.168.1.1"
        with pytest.raises(ValueError, match="leading/trailing whitespace"):
            validate_hue_bridge_ip(invalid_ip)

    def test_rejects_ip_with_trailing_whitespace(self) -> None:
        invalid_ip = "192.168.1.1 "
        with pytest.raises(ValueError, match="leading/trailing whitespace"):
            validate_hue_bridge_ip(invalid_ip)

    def test_rejects_ip_with_too_few_parts(self) -> None:
        invalid_ip = "192.168.1"
        with pytest.raises(ValueError, match="must have 4 parts"):
            validate_hue_bridge_ip(invalid_ip)

    def test_rejects_ip_with_too_many_parts(self) -> None:
        invalid_ip = "192.168.1.1.1"
        with pytest.raises(ValueError, match="must have 4 parts"):
            validate_hue_bridge_ip(invalid_ip)

    def test_rejects_non_numeric_parts(self) -> None:
        invalid_ip = "192.168.abc.1"
        with pytest.raises(ValueError, match="must be numeric"):
            validate_hue_bridge_ip(invalid_ip)

    def test_rejects_part_below_zero(self) -> None:
        invalid_ip = "-1.168.1.1"
        with pytest.raises(ValueError, match="must be between"):
            validate_hue_bridge_ip(invalid_ip)

    def test_rejects_part_above_255(self) -> None:
        invalid_ip = "192.256.1.1"
        with pytest.raises(ValueError, match="must be between"):
            validate_hue_bridge_ip(invalid_ip)

    def test_accepts_minimum_ip_address(self) -> None:
        min_ip = "0.0.0.0"
        assert validate_hue_bridge_ip(min_ip) == min_ip

    def test_accepts_maximum_ip_address(self) -> None:
        max_ip = "255.255.255.255"
        assert validate_hue_bridge_ip(max_ip) == max_ip
