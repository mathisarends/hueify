import re

from pydantic import Field, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from hueify.errors import MissingCredentialsError

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
                f"Hue App Key must have at least {_MIN_APP_KEY_LENGTH} characters"
            )
        if not re.fullmatch(r"[a-zA-Z0-9\-]+", value):
            raise ValueError(
                "Hue App Key must be alphanumeric (letters, digits, and hyphens only)"
            )
        return value


def load_credentials(
    bridge_ip: str | None = None,
    app_key: str | None = None,
) -> HueBridgeCredentials:
    """Read credentials from arguments, the environment and a ``.env`` file.

    Raises:
        MissingCredentialsError: If bridge IP and application key cannot both
            be resolved.
    """
    if bridge_ip is not None and app_key is not None:
        return HueBridgeCredentials(hue_bridge_ip=bridge_ip, hue_app_key=app_key)

    try:
        environment = HueBridgeCredentials()
    except ValidationError as error:
        raise MissingCredentialsError(_MISSING_CREDENTIALS_MESSAGE) from error

    if bridge_ip is None and app_key is None:
        return environment
    return HueBridgeCredentials(
        hue_bridge_ip=bridge_ip or environment.hue_bridge_ip,
        hue_app_key=app_key or environment.hue_app_key,
    )


_MISSING_CREDENTIALS_MESSAGE = (
    "No Hue bridge credentials found.\n"
    "Run `hueify setup` to discover your bridge and register an application "
    "key, then set HUE_BRIDGE_IP and HUE_APP_KEY in your environment or a "
    ".env file.\n"
    "You can also pass bridge_ip and app_key to Hueify() directly."
)
