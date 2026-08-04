import asyncio

from hueify.credentials import save_credentials_config
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


async def _run_setup() -> None:
    print("Hue Bridge Setup\n")

    print("Searching for bridges on your network...")
    bridges = await discover_bridges()

    bridge = _select_bridge(bridges)
    print(f"\nUsing bridge at {bridge.internalipaddress}\n")
    print("Press the link button on your Hue Bridge, then hit Enter.")
    input()

    print("Registering app key...")
    app_key = await register_app_key(bridge.internalipaddress)

    config_path = save_credentials_config(bridge.internalipaddress, app_key)

    print("\nSetup complete!")
    print(f"\nCredentials saved to {config_path}")
    print("\nYou can now use Hueify without setting environment variables.")
    print(
        "\nUse the HUE_BRIDGE_IP/HUE_APP_KEY environment variables to override this file."
    )


def setup() -> None:
    """Interactive onboarding: discover a bridge on the network and register an app key."""
    asyncio.run(_run_setup())
