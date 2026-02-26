from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_MIN_APP_KEY_LENGTH = 20
_IP_ADDRESS_PARTS = 4
_IP_ADDRESS_PART_MIN = 0
_IP_ADDRESS_PART_MAX = 255


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
                f"Hue App Key must be at least {_MIN_APP_KEY_LENGTH} characters, got {len(value)}"
            )

        if not value.isalnum():
            raise ValueError(
                "Hue App Key must be alphanumeric (letters and numbers only)"
            )

        return value
