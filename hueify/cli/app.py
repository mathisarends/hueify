from dataclasses import dataclass

try:
    import typer
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
except ImportError as e:
    raise ImportError(
        "CLI support requires 'typer[all]'. Install with: pip install hueify[cli]"
    ) from e

from hueify import ActionResult

console = Console()
err_console = Console(stderr=True)


@dataclass
class CLIState:
    bridge_ip: str | None = None
    app_key: str | None = None


state = CLIState()

app = typer.Typer(
    name="hueify",
    help="Control your Philips Hue lights from the command line.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)
lights_app = typer.Typer(
    name="lights",
    help="Control individual lights.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)
rooms_app = typer.Typer(
    name="rooms",
    help="Control rooms.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)
zones_app = typer.Typer(
    name="zones",
    help="Control zones.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

app.add_typer(lights_app)
app.add_typer(rooms_app)
app.add_typer(zones_app)


@app.callback()
def configure(
    bridge_ip: str | None = typer.Option(
        None,
        "--bridge-ip",
        envvar="HUE_BRIDGE_IP",
        help="Hue Bridge IP address. Reads [bold]HUE_BRIDGE_IP[/bold] env var if not set.",
    ),
    app_key: str | None = typer.Option(
        None,
        "--app-key",
        envvar="HUE_APP_KEY",
        help="Hue application key. Reads [bold]HUE_APP_KEY[/bold] env var if not set.",
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose logging output."
    ),
) -> None:
    """[bold cyan]Hueify[/bold cyan] — Control your Philips Hue lights from the command line."""
    state.bridge_ip = bridge_ip
    state.app_key = app_key
    if verbose:
        from hueify._logging import configure_logging

        configure_logging("DEBUG")


def print_result(result: ActionResult) -> None:
    if result.success:
        text = Text()
        text.append("✓ ", style="bold green")
        text.append(result.message)
        if result.clamped:
            text.append(" (clamped)", style="yellow")
        console.print(text)
    else:
        text = Text()
        text.append("✗ ", style="bold red")
        text.append(result.message)
        err_console.print(text)
        raise typer.Exit(1)


def print_list(title: str, items: list[str]) -> None:
    if not items:
        console.print(f"[dim]No {title.lower()} found.[/dim]")
        return
    table = Table(
        title=title,
        show_header=False,
        box=None,
        padding=(0, 2),
        title_style="bold cyan",
    )
    table.add_column("Name", style="cyan")
    for item in sorted(items):
        table.add_row(item)
    console.print(table)
    console.print(f"\n[dim]{len(items)} item(s)[/dim]")


def print_resource_info(
    name: str,
    is_on: bool,
    brightness: float,
    temperature: int | None,
) -> None:
    grid = Table.grid(padding=(0, 2))
    grid.add_column(style="dim", min_width=14)
    grid.add_column()

    status_text = (
        Text("ON", style="bold green") if is_on else Text("OFF", style="bold red")
    )
    grid.add_row("Status:", status_text)
    grid.add_row("Brightness:", f"{brightness:.1f}%")
    if temperature is not None:
        grid.add_row("Temperature:", f"{temperature}%")

    console.print(Panel(grid, title=f"[bold cyan]{name}[/bold cyan]", expand=False))


def print_group_info(
    name: str,
    is_on: bool,
    brightness: float,
    temperature: int | None,
    scene_names: list[str],
    active_scene: str | None,
) -> None:
    grid = Table.grid(padding=(0, 2))
    grid.add_column(style="dim", min_width=14)
    grid.add_column()

    status_text = (
        Text("ON", style="bold green") if is_on else Text("OFF", style="bold red")
    )
    grid.add_row("Status:", status_text)
    grid.add_row("Brightness:", f"{brightness:.1f}%")
    if temperature is not None:
        grid.add_row("Temperature:", f"{temperature}%")

    if active_scene:
        grid.add_row("Active Scene:", f"[bold yellow]{active_scene}[/bold yellow]")
    else:
        grid.add_row("Active Scene:", "[dim]none[/dim]")

    if scene_names:
        scenes_text = Text()
        for i, s in enumerate(sorted(scene_names)):
            if i > 0:
                scenes_text.append(", ")
            if s == active_scene:
                scenes_text.append(s, style="bold yellow")
            else:
                scenes_text.append(s, style="cyan")
        grid.add_row("Scenes:", scenes_text)

    console.print(Panel(grid, title=f"[bold cyan]{name}[/bold cyan]", expand=False))


def print_scenes(
    group_name: str, scene_names: list[str], active_scene: str | None
) -> None:
    if not scene_names:
        console.print(f"[dim]No scenes found for '{group_name}'.[/dim]")
        return

    table = Table(
        title=f"Scenes in '{group_name}'",
        show_header=True,
        title_style="bold cyan",
    )
    table.add_column("Scene", style="cyan")
    table.add_column("Status")

    for name in sorted(scene_names):
        if name == active_scene:
            table.add_row(f"[bold]{name}[/bold]", "[bold yellow]● Active[/bold yellow]")
        else:
            table.add_row(name, "[dim]–[/dim]")

    console.print(table)
