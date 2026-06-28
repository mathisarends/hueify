import os
import re
import sys
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)

_MIN_APP_KEY_LENGTH = 20
_IP_ADDRESS_PARTS = 4
_IP_ADDRESS_PART_MIN = 0
_IP_ADDRESS_PART_MAX = 255
_CONFIG_FILE_ENV_VAR = "HUEIFY_CONFIG_FILE"


def get_credentials_config_path() -> Path:
    """Return the per-user config file used by the CLI setup command."""
    if override := os.environ.get(_CONFIG_FILE_ENV_VAR):
        return Path(override).expanduser()

    if os.name == "nt":
        config_root = Path(os.environ.get("APPDATA", Path.home() / "AppData/Roaming"))
    elif sys.platform == "darwin":
        config_root = Path.home() / "Library/Application Support"
    elif xdg_config_home := os.environ.get("XDG_CONFIG_HOME"):
        config_root = Path(xdg_config_home)
    else:
        config_root = Path.home() / ".config"

    return config_root / "hueify" / "config.toml"


def save_credentials_config(bridge_ip: str, app_key: str) -> Path:
    """Persist credentials in the same format HueBridgeCredentials reads."""
    credentials = HueBridgeCredentials(hue_bridge_ip=bridge_ip, hue_app_key=app_key)
    config_path = get_credentials_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        "\n".join(
            (
                f'hue_bridge_ip = "{credentials.hue_bridge_ip}"',
                f'hue_app_key = "{credentials.hue_app_key}"',
                "",
            )
        ),
        encoding="utf-8",
    )
    return config_path


class HueBridgeCredentials(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        populate_by_name=True,
    )

    hue_bridge_ip: str = Field(alias="HUE_BRIDGE_IP")
    hue_app_key: str = Field(alias="HUE_APP_KEY")

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            TomlConfigSettingsSource(settings_cls, get_credentials_config_path()),
            file_secret_settings,
        )

    @field_validator("hue_bridge_ip")
    @classmethod
    def validate_ip(cls, value: str) -> str:
        if not value or value != value.strip():
            raise ValueError(
                "IP address cannot be empty or contain leading/trailing whitespace"
            )

        parts = value.split(".")
        if len(parts) != _IP_ADDRESS_PARTS:
            raise ValueError(
                f"IP address must have {_IP_ADDRESS_PARTS} parts, got {len(parts)}"
            )

        try:
            for part in parts:
                num = int(part)
                if not _IP_ADDRESS_PART_MIN <= num <= _IP_ADDRESS_PART_MAX:
                    raise ValueError(
                        f"IP address part must be between {_IP_ADDRESS_PART_MIN}-{_IP_ADDRESS_PART_MAX}, got {num}"
                    )
        except ValueError as e:
            if "invalid literal" in str(e):
                raise ValueError("IP address parts must be numeric") from e
            raise

        return value

    @field_validator("hue_app_key")
    @classmethod
    def validate_app_key(cls, value: str) -> str:
        if len(value) < _MIN_APP_KEY_LENGTH:
            raise ValueError(
                f"Hue App Key must have at least {_MIN_APP_KEY_LENGTH} characters"
            )
        if not re.fullmatch(r"[a-zA-Z0-9\-]+", value):
            raise ValueError(
                "Hue App Key must be alphanumeric (letters, digits, and hyphens only)"
            )
        return value
