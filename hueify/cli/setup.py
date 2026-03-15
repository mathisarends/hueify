import asyncio

try:
    from rich.console import Console
except ImportError as e:
    raise ImportError(
        "CLI support requires 'typer[all]'. Install with: pip install hueify[cli]"
    ) from e

from hueify.onboarding.discovery import discover_bridge
from hueify.onboarding.registration import register_app_key

console = Console()


async def _run_setup() -> None:
    console.print("[bold]Hue Bridge Setup[/bold]\n")

    with console.status("Searching for bridge on your network..."):
        bridge = await discover_bridge()

    console.print(f"Found bridge at [green]{bridge.internalipaddress}[/green]\n")
    console.print(
        "Press the [bold]link button[/bold] on your Hue Bridge, then hit Enter."
    )
    input()

    with console.status("Registering app key..."):
        app_key = await register_app_key(bridge.internalipaddress)

    console.print("\n[bold green]Setup complete![/bold green]")
    console.print("\nAdd these to your environment:\n")
    console.print(f"  HUE_BRIDGE_IP=[cyan]{bridge.internalipaddress}[/cyan]")
    console.print(f"  HUE_APP_KEY=[cyan]{app_key}[/cyan]")


def setup_command() -> None:
    """Interactive onboarding: discover bridge and register an app key."""
    asyncio.run(_run_setup())
