MIN_BRIGHTNESS = 0
MAX_BRIGHTNESS = 100

MIN_TEMPERATURE_PERCENTAGE = 0
MAX_TEMPERATURE_PERCENTAGE = 100


def normalize_percentage_input(value: float | int) -> int:
    if isinstance(value, int):
        return value

    if 0 <= value <= 1:
        return int(value * 100)

    return int(value)


def clamp_brightness(brightness: int) -> int:
    if brightness < MIN_BRIGHTNESS:
        return MIN_BRIGHTNESS
    elif brightness > MAX_BRIGHTNESS:
        return MAX_BRIGHTNESS
    return brightness


def clamp_temperature_percentage(percentage: int) -> int:
    if percentage < MIN_TEMPERATURE_PERCENTAGE:
        return MIN_TEMPERATURE_PERCENTAGE
    elif percentage > MAX_TEMPERATURE_PERCENTAGE:
        return MAX_TEMPERATURE_PERCENTAGE
    return percentage


def percentage_to_mirek(percentage: int) -> int:
    return int(153 + (percentage / 100) * (500 - 153))


def mirek_to_percentage(mirek: int) -> int:
    return int(((mirek - 153) / (500 - 153)) * 100)


def build_clamped_message(
    property_name: str,
    clamped_value: int,
    requested_value: int,
    unit: str = "",
) -> str:
    return (
        f"{property_name} clamped to {clamped_value}{unit}. "
        f"Requested value {requested_value}{unit} was out of range."
    )
