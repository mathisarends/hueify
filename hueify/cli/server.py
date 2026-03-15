import asyncio
from collections.abc import Awaitable, Callable

try:
    import typer
except ImportError as e:
    raise ImportError(
        "CLI support requires 'typer[all]'. Install with: pip install hueify[cli]"
    ) from e

from hueify import Hueify
from hueify.cli.app import (
    app,
    console,
    err_console,
    lights_app,
    print_group_info,
    print_list,
    print_resource_info,
    print_result,
    print_scenes,
    rooms_app,
    state,
    zones_app,
)
from hueify.cli.setup import setup_command
from hueify.exceptions import HueifyException, ResourceNotFoundException


def _run(coro: Awaitable) -> None:
    try:
        asyncio.run(coro)
    except ResourceNotFoundException as exc:
        err_console.print(f"[red]Not found:[/red] {exc}")
        raise typer.Exit(1) from exc
    except HueifyException as exc:
        err_console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1) from exc
    except KeyboardInterrupt:
        err_console.print("\n[dim]Interrupted.[/dim]")
        raise typer.Exit(130) from None


async def _with_hueify(fn: Callable[[Hueify], Awaitable[None]]) -> None:
    async with Hueify(state.bridge_ip, state.app_key) as hueify:
        await fn(hueify)


@lights_app.command("list")
def lights_list() -> None:
    """List all available lights."""

    async def _cmd(hueify: Hueify) -> None:
        print_list("Lights", hueify.lights.names)

    _run(_with_hueify(_cmd))


@lights_app.command("info")
def lights_info(name: str = typer.Argument(..., help="Light name")) -> None:
    """Show the current state of a light."""

    async def _cmd(hueify: Hueify) -> None:
        light = hueify.lights.from_name(name)
        print_resource_info(
            name=name,
            is_on=light.is_on,
            brightness=light.brightness_percentage,
            temperature=light.color_temperature_percentage,
        )

    _run(_with_hueify(_cmd))


@lights_app.command("on")
def lights_on(name: str = typer.Argument(..., help="Light name")) -> None:
    """Turn on a light."""

    async def _cmd(hueify: Hueify) -> None:
        result = await hueify.lights.turn_on(name)
        print_result(result)

    _run(_with_hueify(_cmd))


@lights_app.command("off")
def lights_off(name: str = typer.Argument(..., help="Light name")) -> None:
    """Turn off a light."""

    async def _cmd(hueify: Hueify) -> None:
        result = await hueify.lights.turn_off(name)
        print_result(result)

    _run(_with_hueify(_cmd))


@lights_app.command("brightness")
def lights_brightness(
    name: str = typer.Argument(..., help="Light name"),
    value: float = typer.Argument(..., help="Brightness percentage (0–100)"),
) -> None:
    """Set a light's brightness to an absolute value."""

    async def _cmd(hueify: Hueify) -> None:
        result = await hueify.lights.set_brightness(name, value)
        print_result(result)

    _run(_with_hueify(_cmd))


@lights_app.command("brightness-up")
def lights_brightness_up(
    name: str = typer.Argument(..., help="Light name"),
    value: float = typer.Argument(..., help="Amount to increase brightness by (0–100)"),
) -> None:
    """Increase a light's brightness by a relative amount."""

    async def _cmd(hueify: Hueify) -> None:
        result = await hueify.lights.increase_brightness(name, value)
        print_result(result)

    _run(_with_hueify(_cmd))


@lights_app.command("brightness-down")
def lights_brightness_down(
    name: str = typer.Argument(..., help="Light name"),
    value: float = typer.Argument(..., help="Amount to decrease brightness by (0–100)"),
) -> None:
    """Decrease a light's brightness by a relative amount."""

    async def _cmd(hueify: Hueify) -> None:
        result = await hueify.lights.decrease_brightness(name, value)
        print_result(result)

    _run(_with_hueify(_cmd))


@lights_app.command("brightness-get")
def lights_brightness_get(
    name: str = typer.Argument(..., help="Light name"),
) -> None:
    """Get the current brightness of a light."""

    async def _cmd(hueify: Hueify) -> None:
        brightness = hueify.lights.get_brightness(name)
        console.print(f"[cyan]{name}[/cyan] brightness: [bold]{brightness:.1f}%[/bold]")

    _run(_with_hueify(_cmd))


@lights_app.command("temperature")
def lights_temperature(
    name: str = typer.Argument(..., help="Light name"),
    value: float = typer.Argument(
        ..., help="Color temperature percentage (0=warm, 100=cool)"
    ),
) -> None:
    """Set a light's color temperature (0 = warmest, 100 = coolest)."""

    async def _cmd(hueify: Hueify) -> None:
        result = await hueify.lights.set_color_temperature(name, value)
        print_result(result)

    _run(_with_hueify(_cmd))


@rooms_app.command("list")
def rooms_list() -> None:
    """List all available rooms."""

    async def _cmd(hueify: Hueify) -> None:
        print_list("Rooms", hueify.rooms.names)

    _run(_with_hueify(_cmd))


@rooms_app.command("info")
def rooms_info(name: str = typer.Argument(..., help="Room name")) -> None:
    """Show the current state of a room."""

    async def _cmd(hueify: Hueify) -> None:
        room = hueify.rooms.from_name(name)
        active = room.get_active_scene()
        print_group_info(
            name=name,
            is_on=room.is_on,
            brightness=room.brightness_percentage,
            temperature=room.color_temperature_percentage,
            scene_names=room.scene_names,
            active_scene=active.name if active else None,
        )

    _run(_with_hueify(_cmd))


@rooms_app.command("on")
def rooms_on(name: str = typer.Argument(..., help="Room name")) -> None:
    """Turn on all lights in a room."""

    async def _cmd(hueify: Hueify) -> None:
        result = await hueify.rooms.turn_on(name)
        print_result(result)

    _run(_with_hueify(_cmd))


@rooms_app.command("off")
def rooms_off(name: str = typer.Argument(..., help="Room name")) -> None:
    """Turn off all lights in a room."""

    async def _cmd(hueify: Hueify) -> None:
        result = await hueify.rooms.turn_off(name)
        print_result(result)

    _run(_with_hueify(_cmd))


@rooms_app.command("brightness")
def rooms_brightness(
    name: str = typer.Argument(..., help="Room name"),
    value: float = typer.Argument(..., help="Brightness percentage (0–100)"),
) -> None:
    """Set a room's brightness to an absolute value."""

    async def _cmd(hueify: Hueify) -> None:
        result = await hueify.rooms.set_brightness(name, value)
        print_result(result)

    _run(_with_hueify(_cmd))


@rooms_app.command("brightness-up")
def rooms_brightness_up(
    name: str = typer.Argument(..., help="Room name"),
    value: float = typer.Argument(..., help="Amount to increase brightness by (0–100)"),
) -> None:
    """Increase a room's brightness by a relative amount."""

    async def _cmd(hueify: Hueify) -> None:
        result = await hueify.rooms.increase_brightness(name, value)
        print_result(result)

    _run(_with_hueify(_cmd))


@rooms_app.command("brightness-down")
def rooms_brightness_down(
    name: str = typer.Argument(..., help="Room name"),
    value: float = typer.Argument(..., help="Amount to decrease brightness by (0–100)"),
) -> None:
    """Decrease a room's brightness by a relative amount."""

    async def _cmd(hueify: Hueify) -> None:
        result = await hueify.rooms.decrease_brightness(name, value)
        print_result(result)

    _run(_with_hueify(_cmd))


@rooms_app.command("brightness-get")
def rooms_brightness_get(
    name: str = typer.Argument(..., help="Room name"),
) -> None:
    """Get the current brightness of a room."""

    async def _cmd(hueify: Hueify) -> None:
        brightness = hueify.rooms.get_brightness(name)
        console.print(f"[cyan]{name}[/cyan] brightness: [bold]{brightness:.1f}%[/bold]")

    _run(_with_hueify(_cmd))


@rooms_app.command("temperature")
def rooms_temperature(
    name: str = typer.Argument(..., help="Room name"),
    value: float = typer.Argument(
        ..., help="Color temperature percentage (0=warm, 100=cool)"
    ),
) -> None:
    """Set a room's color temperature (0 = warmest, 100 = coolest)."""

    async def _cmd(hueify: Hueify) -> None:
        result = await hueify.rooms.set_color_temperature(name, value)
        print_result(result)

    _run(_with_hueify(_cmd))


@rooms_app.command("scenes")
def rooms_scenes(name: str = typer.Argument(..., help="Room name")) -> None:
    """List all scenes available in a room."""

    async def _cmd(hueify: Hueify) -> None:
        room = hueify.rooms.from_name(name)
        active = room.get_active_scene()
        print_scenes(name, room.scene_names, active.name if active else None)

    _run(_with_hueify(_cmd))


@rooms_app.command("active-scene")
def rooms_active_scene(name: str = typer.Argument(..., help="Room name")) -> None:
    """Show the currently active scene in a room."""

    async def _cmd(hueify: Hueify) -> None:
        room = hueify.rooms.from_name(name)
        active = room.get_active_scene()
        if active:
            console.print(
                f"Active scene in [cyan]{name}[/cyan]: [bold yellow]{active.name}[/bold yellow]"
            )
        else:
            console.print(f"[dim]No active scene in '{name}'.[/dim]")

    _run(_with_hueify(_cmd))


@rooms_app.command("activate-scene")
def rooms_activate_scene(
    name: str = typer.Argument(..., help="Room name"),
    scene: str = typer.Argument(..., help="Scene name"),
) -> None:
    """Activate a scene in a room."""

    async def _cmd(hueify: Hueify) -> None:
        result = await hueify.rooms.activate_scene(name, scene)
        print_result(result)

    _run(_with_hueify(_cmd))


@zones_app.command("list")
def zones_list() -> None:
    """List all available zones."""

    async def _cmd(hueify: Hueify) -> None:
        print_list("Zones", hueify.zones.names)

    _run(_with_hueify(_cmd))


@zones_app.command("info")
def zones_info(name: str = typer.Argument(..., help="Zone name")) -> None:
    """Show the current state of a zone."""

    async def _cmd(hueify: Hueify) -> None:
        zone = hueify.zones.from_name(name)
        active = zone.get_active_scene()
        print_group_info(
            name=name,
            is_on=zone.is_on,
            brightness=zone.brightness_percentage,
            temperature=zone.color_temperature_percentage,
            scene_names=zone.scene_names,
            active_scene=active.name if active else None,
        )

    _run(_with_hueify(_cmd))


@zones_app.command("on")
def zones_on(name: str = typer.Argument(..., help="Zone name")) -> None:
    """Turn on all lights in a zone."""

    async def _cmd(hueify: Hueify) -> None:
        result = await hueify.zones.turn_on(name)
        print_result(result)

    _run(_with_hueify(_cmd))


@zones_app.command("off")
def zones_off(name: str = typer.Argument(..., help="Zone name")) -> None:
    """Turn off all lights in a zone."""

    async def _cmd(hueify: Hueify) -> None:
        result = await hueify.zones.turn_off(name)
        print_result(result)

    _run(_with_hueify(_cmd))


@zones_app.command("brightness")
def zones_brightness(
    name: str = typer.Argument(..., help="Zone name"),
    value: float = typer.Argument(..., help="Brightness percentage (0–100)"),
) -> None:
    """Set a zone's brightness to an absolute value."""

    async def _cmd(hueify: Hueify) -> None:
        result = await hueify.zones.set_brightness(name, value)
        print_result(result)

    _run(_with_hueify(_cmd))


@zones_app.command("brightness-up")
def zones_brightness_up(
    name: str = typer.Argument(..., help="Zone name"),
    value: float = typer.Argument(..., help="Amount to increase brightness by (0–100)"),
) -> None:
    """Increase a zone's brightness by a relative amount."""

    async def _cmd(hueify: Hueify) -> None:
        result = await hueify.zones.increase_brightness(name, value)
        print_result(result)

    _run(_with_hueify(_cmd))


@zones_app.command("brightness-down")
def zones_brightness_down(
    name: str = typer.Argument(..., help="Zone name"),
    value: float = typer.Argument(..., help="Amount to decrease brightness by (0–100)"),
) -> None:
    """Decrease a zone's brightness by a relative amount."""

    async def _cmd(hueify: Hueify) -> None:
        result = await hueify.zones.decrease_brightness(name, value)
        print_result(result)

    _run(_with_hueify(_cmd))


@zones_app.command("brightness-get")
def zones_brightness_get(
    name: str = typer.Argument(..., help="Zone name"),
) -> None:
    """Get the current brightness of a zone."""

    async def _cmd(hueify: Hueify) -> None:
        brightness = hueify.zones.get_brightness(name)
        console.print(f"[cyan]{name}[/cyan] brightness: [bold]{brightness:.1f}%[/bold]")

    _run(_with_hueify(_cmd))


@zones_app.command("temperature")
def zones_temperature(
    name: str = typer.Argument(..., help="Zone name"),
    value: float = typer.Argument(
        ..., help="Color temperature percentage (0=warm, 100=cool)"
    ),
) -> None:
    """Set a zone's color temperature (0 = warmest, 100 = coolest)."""

    async def _cmd(hueify: Hueify) -> None:
        result = await hueify.zones.set_color_temperature(name, value)
        print_result(result)

    _run(_with_hueify(_cmd))


@zones_app.command("scenes")
def zones_scenes(name: str = typer.Argument(..., help="Zone name")) -> None:
    """List all scenes available in a zone."""

    async def _cmd(hueify: Hueify) -> None:
        zone = hueify.zones.from_name(name)
        active = zone.get_active_scene()
        print_scenes(name, zone.scene_names, active.name if active else None)

    _run(_with_hueify(_cmd))


@zones_app.command("active-scene")
def zones_active_scene(name: str = typer.Argument(..., help="Zone name")) -> None:
    """Show the currently active scene in a zone."""

    async def _cmd(hueify: Hueify) -> None:
        zone = hueify.zones.from_name(name)
        active = zone.get_active_scene()
        if active:
            console.print(
                f"Active scene in [cyan]{name}[/cyan]: [bold yellow]{active.name}[/bold yellow]"
            )
        else:
            console.print(f"[dim]No active scene in '{name}'.[/dim]")

    _run(_with_hueify(_cmd))


@zones_app.command("activate-scene")
def zones_activate_scene(
    name: str = typer.Argument(..., help="Zone name"),
    scene: str = typer.Argument(..., help="Scene name"),
) -> None:
    """Activate a scene in a zone."""

    async def _cmd(hueify: Hueify) -> None:
        result = await hueify.zones.activate_scene(name, scene)
        print_result(result)

    _run(_with_hueify(_cmd))


@app.command("setup")
def setup() -> None:
    """Interactive onboarding: discover bridge and register an app key."""
    setup_command()


def main() -> None:
    app()
