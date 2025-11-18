from pathlib import Path


def read_env_file(env_path: Path = Path(".env")) -> dict[str, str]:
    if not env_path.exists():
        return {}

    env_vars = {}
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            env_vars[key.strip()] = value.strip()
    return env_vars


def write_env_file(updates: dict[str, str], env_path: Path = Path(".env")) -> None:
    env_vars = read_env_file(env_path)
    env_vars.update(updates)

    lines = [f"{key}={value}" for key, value in env_vars.items()]
    env_path.write_text("\n".join(lines) + "\n")
