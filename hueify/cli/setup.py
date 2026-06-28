import asyncio

try:
    from rich.console import Console
except ImportError as e:
    raise ImportError(
        "CLI support requires 'typer[all]'. Install with: pip install hueify[cli]"
    ) from e

from hueify.credentials import save_credentials_config
from hueify.onboarding.discovery import DiscoveredBridge, discover_bridges
from hueify.onboarding.registration import register_app_key

console = Console()


def _select_bridge(bridges: list[DiscoveredBridge]) -> DiscoveredBridge:
    if len(bridges) == 1:
        return bridges[0]

    console.print(f"Found [bold]{len(bridges)}[/bold] bridges:\n")
    for i, b in enumerate(bridges, 1):
        console.print(f"  [{i}] {b.internalipaddress}  [dim]({b.id})[/dim]")
    console.print()

    while True:
        choice = input(f"Select a bridge (1-{len(bridges)}): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(bridges):
            return bridges[int(choice) - 1]
        console.print("[red]Invalid choice, try again.[/red]")


async def _run_setup() -> None:
    console.print("[bold]Hue Bridge Setup[/bold]\n")

    with console.status("Searching for bridges on your network..."):
        bridges = await discover_bridges()

    bridge = _select_bridge(bridges)
    console.print(f"\nUsing bridge at [green]{bridge.internalipaddress}[/green]\n")
    console.print(
        "Press the [bold]link button[/bold] on your Hue Bridge, then hit Enter."
    )
    input()

    with console.status("Registering app key..."):
        app_key = await register_app_key(bridge.internalipaddress)

    config_path = save_credentials_config(bridge.internalipaddress, app_key)

    console.print("\n[bold green]Setup complete![/bold green]")
    console.print(f"\nCredentials saved to [cyan]{config_path}[/cyan]")
    console.print(
        "\nYou can now run commands like [bold]hueify lights list[/bold] without setting environment variables."
    )
    console.print(
        "\nUse [bold]--bridge-ip[/bold]/[bold]--app-key[/bold] or the [bold]HUE_BRIDGE_IP[/bold]/[bold]HUE_APP_KEY[/bold] environment variables to override this file."
    )


def setup_command() -> None:
    """Interactive onboarding: discover bridge and register an app key."""
    asyncio.run(_run_setup())
