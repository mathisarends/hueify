from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from hueify.credentials.utils import validate_hue_app_key, validate_hue_bridge_ip


class HueBridgeCredentials(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    hue_bridge_ip: str | None = Field(default=None, alias="HUE_BRIDGE_IP")
    hue_app_key: str | None = Field(default=None, alias="HUE_APP_KEY")

    @field_validator("hue_bridge_ip")
    @classmethod
    def validate_ip(cls, value: str | None) -> str | None:
        return validate_hue_bridge_ip(value)

    @field_validator("hue_app_key")
    @classmethod
    def validate_app_key(cls, value: str | None) -> str | None:
        return validate_hue_app_key(value)
