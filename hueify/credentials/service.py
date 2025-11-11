from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class HueBridgeCredentials(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )
    
    hue_bridge_ip: str | None = Field(default=None, alias="HUE_BRIDGE_IP")
    hue_user_id: str | None = Field(default=None, alias="HUE_USER_ID")
    
    @field_validator("hue_bridge_ip")
    @classmethod
    def validate_ip(cls, value: str | None) -> str | None:
        if value is None:
            return value
            
        if not value or value != value.strip():
            raise ValueError("IP address cannot be empty or contain leading/trailing whitespace")
        
        parts = value.split(".")
        if len(parts) != 4:
            raise ValueError(f"IP address must have 4 parts, got {len(parts)}")
        
        try:
            for part in parts:
                num = int(part)
                if not 0 <= num <= 255:
                    raise ValueError(f"IP address part must be between 0-255, got {num}")
        except ValueError as e:
            if "invalid literal" in str(e):
                raise ValueError(f"IP address parts must be numeric")
            raise
        
        return value
    
    @field_validator("hue_user_id")
    @classmethod
    def validate_user_id(cls, value: str | None) -> str | None:
        if value is None:
            return value

        if len(value) < 20:
            raise ValueError(f"User ID must be at least 20 characters, got {len(value)}")

        if not value.isalnum():
            raise ValueError("User ID must be alphanumeric (letters and numbers only)")

        return value