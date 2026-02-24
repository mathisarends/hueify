import pytest
from pydantic import ValidationError

from hueify.credentials import HueBridgeCredentials

VALID_IP = "192.168.1.1"
VALID_APP_KEY = "a" * 20


class TestHueBridgeIpValidation:
    def _make(self, ip: str) -> HueBridgeCredentials:
        return HueBridgeCredentials(HUE_BRIDGE_IP=ip, HUE_APP_KEY=VALID_APP_KEY)

    def test_valid_ip(self):
        credentials = self._make(VALID_IP)
        assert credentials.hue_bridge_ip == VALID_IP

    def test_valid_ip_edge_cases(self):
        assert self._make("0.0.0.0").hue_bridge_ip == "0.0.0.0"
        assert self._make("255.255.255.255").hue_bridge_ip == "255.255.255.255"

    def test_invalid_ip_leading_whitespace(self):
        with pytest.raises(ValidationError, match="leading/trailing whitespace"):
            self._make(" 192.168.1.1")

    def test_invalid_ip_trailing_whitespace(self):
        with pytest.raises(ValidationError, match="leading/trailing whitespace"):
            self._make("192.168.1.1 ")

    def test_invalid_ip_too_few_parts(self):
        with pytest.raises(ValidationError, match="must have 4 parts"):
            self._make("192.168.1")

    def test_invalid_ip_too_many_parts(self):
        with pytest.raises(ValidationError, match="must have 4 parts"):
            self._make("192.168.1.1.1")

    def test_invalid_ip_part_out_of_range(self):
        with pytest.raises(ValidationError, match="between 0-255"):
            self._make("192.168.1.256")

    def test_invalid_ip_negative_part(self):
        with pytest.raises(ValidationError, match="between 0-255"):
            self._make("192.168.-1.1")

    def test_invalid_ip_non_numeric_parts(self):
        with pytest.raises(ValidationError, match="must be numeric"):
            self._make("192.168.abc.1")

    def test_invalid_ip_empty(self):
        with pytest.raises(ValidationError, match="cannot be empty"):
            self._make("")


class TestHueAppKeyValidation:
    def _make(self, app_key: str) -> HueBridgeCredentials:
        return HueBridgeCredentials(HUE_BRIDGE_IP=VALID_IP, HUE_APP_KEY=app_key)

    def test_valid_app_key(self):
        credentials = self._make(VALID_APP_KEY)
        assert credentials.hue_app_key == VALID_APP_KEY

    def test_valid_app_key_exactly_min_length(self):
        key = "b" * 20
        assert self._make(key).hue_app_key == key

    def test_valid_app_key_longer_than_min(self):
        key = "c" * 40
        assert self._make(key).hue_app_key == key

    def test_invalid_app_key_too_short(self):
        with pytest.raises(ValidationError, match="at least 20 characters"):
            self._make("tooshort")

    def test_invalid_app_key_non_alphanumeric(self):
        with pytest.raises(ValidationError, match="alphanumeric"):
            self._make("a" * 19 + "!")

    def test_invalid_app_key_with_spaces(self):
        with pytest.raises(ValidationError, match="alphanumeric"):
            self._make("a" * 19 + " ")
