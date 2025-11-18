MIN_APP_KEY_LENGTH = 20
IP_ADDRESS_PARTS = 4
IP_ADDRESS_PART_MIN = 0
IP_ADDRESS_PART_MAX = 255


def validate_hue_app_key(value: str) -> str:
    if len(value) < MIN_APP_KEY_LENGTH:
        raise ValueError(
            f"Hue App Key must be at least {MIN_APP_KEY_LENGTH} characters, got {len(value)}"
        )

    if not value.isalnum():
        raise ValueError("Hue App Key must be alphanumeric (letters and numbers only)")

    return value


def validate_hue_bridge_ip(value: str) -> str:
    if value is None:
        return value

    if not value or value != value.strip():
        raise ValueError(
            "IP address cannot be empty or contain leading/trailing whitespace"
        )

    parts = value.split(".")
    if len(parts) != IP_ADDRESS_PARTS:
        raise ValueError(
            f"IP address must have {IP_ADDRESS_PARTS} parts, got {len(parts)}"
        )

    try:
        for part in parts:
            num = int(part)
            if not IP_ADDRESS_PART_MIN <= num <= IP_ADDRESS_PART_MAX:
                raise ValueError(
                    f"IP address part must be between {IP_ADDRESS_PART_MIN}-{IP_ADDRESS_PART_MAX}, got {num}"
                )
    except ValueError as e:
        if "invalid literal" in str(e):
            raise ValueError("IP address parts must be numeric") from e
        raise

    return value
