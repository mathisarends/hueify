import asyncio
import sys
from pathlib import Path

import httpx

from hueify.setup.models import BridgeListAdapter
from hueify.setup.utils import write_env_file


async def discover_bridge_ip() -> str | None:
    async with httpx.AsyncClient() as client:
        response = await client.get("https://discovery.meethue.com/", timeout=10.0)
        response.raise_for_status()
        bridge_discovery_response = BridgeListAdapter.validate_python(response.json())
        return bridge_discovery_response[0].internalipaddress


async def create_api_user(bridge_ip: str) -> str | None:
    url = f"http://{bridge_ip}/api"
    payload = {"devicetype": "hueify#user"}

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)
        data = response.json()

    if not isinstance(data, list) or not data:
        return None

    result = data[0]

    if "success" in result:
        return result["success"]["username"]

    return None


def wait_for_button_press() -> None:
    print("\n⚠  Press the link button on your Hue Bridge")
    print("   (You have 30 seconds after pressing)")
    input("\nPress Enter when ready...")


def save_credentials(
    bridge_ip: str, app_key: str, env_path: Path = Path(".env")
) -> None:
    write_env_file(
        {"HUE_BRIDGE_IP": bridge_ip, "HUE_APP_KEY": app_key},
        env_path,
    )


async def run_setup() -> bool:
    print("Hue Bridge Setup")
    print("=" * 50)

    print("\n🔍 Discovering Hue Bridge...")
    bridge_ip = await discover_bridge_ip()

    if not bridge_ip:
        print("✗ No Hue Bridge found on your network")
        return False

    print(f"✓ Found bridge at {bridge_ip}")

    wait_for_button_press()

    print("\n🔑 Creating API user...")
    app_key = await create_api_user(bridge_ip)

    if not app_key:
        print("✗ Failed to create API user")
        print("  Make sure you pressed the link button")
        return False

    print("✓ API user created")

    save_credentials(bridge_ip, app_key)
    print("\n✓ Credentials saved to .env")
    print(f"  HUE_BRIDGE_IP={bridge_ip}")
    print(f"  HUE_APP_KEY={app_key[:8]}...")
    print("\n✓ Setup complete")

    return True


async def main() -> None:
    try:
        success = await run_setup()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n✗ Setup cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
