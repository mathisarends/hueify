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
    print("\nSetup complete. Hueify reads these two values:\n")
    print(f"  HUE_BRIDGE_IP={credentials.hue_bridge_ip}")
    print(f"  HUE_APP_KEY={credentials.hue_app_key}")
    print(
        "\nSet them in your environment or write them to a .env file.\n"
        "The app key controls your bridge - keep it out of version control."
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
    app_key = await register_app_key(bridge.internalipaddress)

    credentials = HueBridgeCredentials(
        hue_bridge_ip=bridge.internalipaddress,
        hue_app_key=app_key,
    )
    _print_credentials(credentials)
    return credentials


def setup() -> HueBridgeCredentials:
    """Run the interactive onboarding and return the resulting credentials."""
    return asyncio.run(_run_setup())
