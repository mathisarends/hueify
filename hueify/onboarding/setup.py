import asyncio

from hueify.credentials import HueBridgeCredentials
from hueify.onboarding.discovery import DiscoveredBridge, discover_bridges
from hueify.onboarding.registration import register_app_key


def _select_bridge(bridges: list[DiscoveredBridge]) -> DiscoveredBridge:
    if len(bridges) == 1:
        return bridges[0]

    print(f"Found {len(bridges)} bridges:\n")
    for i, b in enumerate(bridges, 1):
        print(f"  [{i}] {b.internalipaddress}  ({b.id})")
    print()

    while True:
        choice = input(f"Select a bridge (1-{len(bridges)}): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(bridges):
            return bridges[int(choice) - 1]
        print("Invalid choice, try again.")


def _print_credentials(credentials: HueBridgeCredentials) -> None:
    print("\nSetup complete. Hueify reads these values:\n")
    print(f"  HUE_BRIDGE_IP={credentials.hue_bridge_ip}")
    print(f"  HUE_APP_KEY={credentials.hue_app_key}")
    if credentials.hue_client_key is not None:
        print(f"  HUE_CLIENT_KEY={credentials.hue_client_key}")
    print(
        "\nSet them in your environment or write them to a .env file.\n"
        "These keys control your bridge - keep them out of version control."
    )
    if credentials.hue_client_key is None:
        print(
            "\nThe bridge did not return a client key, so entertainment streaming "
            "is unavailable. Run the setup again to get one."
        )
    else:
        print(
            "\nThe client key is only needed for entertainment streaming, and the "
            "bridge never shows it again."
        )


async def _run_setup() -> HueBridgeCredentials:
    print("Hue Bridge Setup\n")

    print("Searching for bridges on your network...")
    bridges = await discover_bridges()

    bridge = _select_bridge(bridges)
    print(f"\nUsing bridge at {bridge.internalipaddress}\n")
    print("Press the link button on your Hue Bridge, then hit Enter.")
    input()

    print("Registering app key...")
    app = await register_app_key(bridge.internalipaddress)

    credentials = HueBridgeCredentials(
        hue_bridge_ip=bridge.internalipaddress,
        hue_app_key=app.app_key,
        hue_client_key=app.client_key,
    )
    _print_credentials(credentials)
    return credentials


def setup() -> HueBridgeCredentials:
    """Run the interactive onboarding and return the resulting credentials."""
    return asyncio.run(_run_setup())
