import pytest
from pydantic import ValidationError

from hueify import Hueify, MissingCredentialsError
from hueify.credentials import HueBridgeCredentials, load_credentials

VALID_IP = "192.168.1.1"
VALID_APP_KEY = "a" * 20
OTHER_IP = "192.168.1.10"
OTHER_APP_KEY = "b" * 20


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


class TestCredentialSources:
    def test_reads_credentials_from_a_dotenv_file(self, tmp_path, monkeypatch):
        (tmp_path / ".env").write_text(
            f"HUE_BRIDGE_IP={OTHER_IP}\nHUE_APP_KEY={OTHER_APP_KEY}\n",
            encoding="utf-8",
        )
        monkeypatch.delenv("HUE_BRIDGE_IP", raising=False)
        monkeypatch.delenv("HUE_APP_KEY", raising=False)
        monkeypatch.chdir(tmp_path)

        credentials = load_credentials()

        assert credentials.hue_bridge_ip == OTHER_IP
        assert credentials.hue_app_key == OTHER_APP_KEY

    def test_environment_overrides_the_dotenv_file(self, tmp_path, monkeypatch):
        (tmp_path / ".env").write_text(
            f"HUE_BRIDGE_IP={OTHER_IP}\nHUE_APP_KEY={OTHER_APP_KEY}\n",
            encoding="utf-8",
        )
        monkeypatch.setenv("HUE_BRIDGE_IP", VALID_IP)
        monkeypatch.setenv("HUE_APP_KEY", VALID_APP_KEY)
        monkeypatch.chdir(tmp_path)

        credentials = load_credentials()

        assert credentials.hue_bridge_ip == VALID_IP
        assert credentials.hue_app_key == VALID_APP_KEY

    def test_hueify_combines_partial_explicit_credentials_with_the_environment(
        self, monkeypatch
    ):
        monkeypatch.setenv("HUE_BRIDGE_IP", VALID_IP)
        monkeypatch.setenv("HUE_APP_KEY", VALID_APP_KEY)

        hue = Hueify(bridge_ip=OTHER_IP)

        assert hue._credentials.hue_bridge_ip == OTHER_IP
        assert hue._credentials.hue_app_key == VALID_APP_KEY


class TestMissingCredentials:
    def test_load_credentials_points_at_the_setup_command(
        self, without_stored_credentials
    ):
        with pytest.raises(MissingCredentialsError, match="hueify setup"):
            load_credentials()

    def test_load_credentials_names_the_variables_to_set(
        self, without_stored_credentials
    ):
        with pytest.raises(MissingCredentialsError) as error:
            load_credentials()

        assert "HUE_BRIDGE_IP" in str(error.value)
        assert "HUE_APP_KEY" in str(error.value)

    def test_constructing_hueify_raises_missing_credentials_error(
        self, without_stored_credentials
    ):
        with pytest.raises(MissingCredentialsError):
            Hueify()

    def test_explicit_credentials_need_no_environment(self, without_stored_credentials):
        credentials = load_credentials(VALID_IP, VALID_APP_KEY)

        assert credentials.hue_bridge_ip == VALID_IP
        assert credentials.hue_app_key == VALID_APP_KEY
