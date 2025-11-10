def is_valid_ip(ip: str) -> bool:
    parts = ip.split(".")
    if len(parts) != 4:
        return False
    try:
        return all(0 <= int(part) <= 255 for part in parts)
    except ValueError:
        return False


def is_valid_user_id(user_id: str) -> bool:
    return len(user_id) >= 20 and user_id.isalnum()
