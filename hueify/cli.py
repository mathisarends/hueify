"""The optional, shell-friendly ``hueify`` command line interface."""

import asyncio
import json
import sys
from dataclasses import dataclass
from importlib.metadata import version
from typing import Any, NoReturn
from uuid import UUID

try:
    import typer
    from rich.console import Console
    from rich.table import Table
except ImportError:  # pragma: no cover - exercised without the optional extra
    typer = None

from hueify import Hueify
from hueify.errors import HueifyError

_CLI_EXTRA_MESSAGE = (
    "Install the command line interface with: pip install 'hueify[cli]'"
)


@dataclass(frozen=True, slots=True)
class OutputOptions:
    """Global output settings, shared by every command."""

    json: bool
    plain: bool
    no_color: bool


def _missing_cli_extra() -> NoReturn:
    print(_CLI_EXTRA_MESSAGE, file=sys.stderr)
    raise SystemExit(1)


def _print_json(value: Any) -> None:
    print(json.dumps(value, default=str, indent=2, sort_keys=True))


def _resource_json(resource: Any) -> Any:
    if hasattr(resource, "model_dump"):
        return resource.model_dump(mode="json")
    return resource


def _resource_state(resource: Any) -> str:
    state = getattr(resource, "is_on", None)
    if state is not None:
        return "on" if state else "off"
    status = getattr(resource, "status", None)
    return "" if status is None else str(status)


def _write_resources(context: Any, resources: list[Any], title: str) -> None:
    output = context.obj
    assert isinstance(output, OutputOptions)
    if output.json:
        _print_json([_resource_json(resource) for resource in resources])
        return

    rows = [
        (str(resource.id), resource.name, _resource_state(resource))
        for resource in resources
    ]
    if output.plain:
        for row in rows:
            typer.echo("\t".join(row))
        return

    table = Table(title=title)
    table.add_column("ID")
    table.add_column("Name")
    table.add_column("State")
    for row in rows:
        table.add_row(*row)
    Console(no_color=output.no_color).print(table)


async def _list_resources(namespace_name: str) -> list[Any]:
    async with Hueify() as hue:
        response = await getattr(hue, namespace_name).list()
    return response.data


def _run(coroutine: Any) -> Any:
    try:
        return asyncio.run(coroutine)
    except HueifyError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(1) from error


async def _resolve_target(namespace: Any, target: str) -> UUID | str:
    try:
        UUID(target)
    except ValueError:
        return (await namespace.find_by_name(target)).id
    return target


async def _control(
    namespace_name: str,
    action: str,
    target: str,
    *args: Any,
    **kwargs: Any,
) -> Any:
    async with Hueify() as hue:
        namespace = getattr(hue, namespace_name)
        resource_id = await _resolve_target(namespace, target)
        return await getattr(namespace, action)(resource_id, *args, **kwargs)


def _write_response(context: Any, response: Any) -> None:
    output = context.obj
    assert isinstance(output, OutputOptions)
    if output.json:
        _print_json(_resource_json(response))
        return

    identifiers = getattr(response, "data", [])
    if output.plain:
        for identifier in identifiers:
            typer.echo(f"{identifier.rid}\t{identifier.rtype}")
        return
    typer.echo(f"Updated {len(identifiers)} resource(s).")


if typer is not None:
    app = typer.Typer(
        name="hueify",
        help="Control Philips Hue bridges from the command line.",
        no_args_is_help=True,
        rich_markup_mode="markdown",
    )

    @app.callback()
    def callback(
        context: typer.Context,
        json_output: bool = typer.Option(
            False,
            "--json",
            help="Write stable JSON to stdout.",
        ),
        plain: bool = typer.Option(
            False,
            "--plain",
            help="Write stable, tab-separated output to stdout.",
        ),
        no_color: bool = typer.Option(
            False,
            "--no-color",
            help="Disable colour in human output.",
        ),
        show_version: bool = typer.Option(
            False,
            "--version",
            is_eager=True,
            help="Show the Hueify version and exit.",
        ),
    ) -> None:
        """Global flags apply before every Hue command."""
        if show_version:
            typer.echo(version("hueify"))
            raise typer.Exit()
        if json_output and plain:
            raise typer.BadParameter("Choose either --json or --plain, not both")
        context.obj = OutputOptions(json=json_output, plain=plain, no_color=no_color)

    @app.command()
    def setup() -> None:
        """Discover a bridge and register the application interactively."""
        from hueify.onboarding.setup import setup as run_setup

        run_setup()

    @app.command()
    def version_info(context: typer.Context) -> None:
        """Show the installed Hueify version in the selected output mode."""
        output = context.obj
        assert isinstance(output, OutputOptions)
        if output.json:
            _print_json({"version": version("hueify")})
        elif output.plain:
            typer.echo(version("hueify"))
        else:
            typer.echo(f"Hueify {version('hueify')}")

    light_app = typer.Typer(help="Inspect and control individual lights.")
    room_app = typer.Typer(help="Inspect and control rooms.")
    zone_app = typer.Typer(help="Inspect and control zones.")
    scene_app = typer.Typer(help="Inspect and activate scenes.")
    entertainment_app = typer.Typer(help="Inspect entertainment areas.")
    app.add_typer(light_app, name="light")
    app.add_typer(room_app, name="room")
    app.add_typer(zone_app, name="zone")
    app.add_typer(scene_app, name="scene")
    app.add_typer(entertainment_app, name="entertainment")

    @light_app.command("list")
    def list_lights(context: typer.Context) -> None:
        """List all lights visible to the configured bridge."""
        _write_resources(context, _run(_list_resources("lights")), "Lights")

    @room_app.command("list")
    def list_rooms(context: typer.Context) -> None:
        """List all rooms visible to the configured bridge."""
        _write_resources(context, _run(_list_resources("rooms")), "Rooms")

    @zone_app.command("list")
    def list_zones(context: typer.Context) -> None:
        """List all zones visible to the configured bridge."""
        _write_resources(context, _run(_list_resources("zones")), "Zones")

    @scene_app.command("list")
    def list_scenes(context: typer.Context) -> None:
        """List scenes visible to the configured bridge."""
        _write_resources(context, _run(_list_resources("scenes")), "Scenes")

    @entertainment_app.command("list")
    def list_entertainment_areas(context: typer.Context) -> None:
        """List entertainment areas and whether they are streaming."""
        _write_resources(
            context,
            _run(_list_resources("entertainment")),
            "Entertainment areas",
        )

    def add_control_commands(command_app: typer.Typer, namespace_name: str) -> None:
        @command_app.command("on")
        def turn_on(
            context: typer.Context,
            target: str = typer.Argument(help="A resource UUID or name."),
            brightness: float | None = typer.Option(
                None, "--brightness", "-b", help="Brightness in percent."
            ),
            transition: float | None = typer.Option(
                None, "--transition", help="Fade duration in seconds."
            ),
        ) -> None:
            """Turn a light, room, or zone on."""
            _write_response(
                context,
                _run(
                    _control(
                        namespace_name,
                        "turn_on",
                        target,
                        brightness=brightness,
                        transition=transition,
                    )
                ),
            )

        @command_app.command("off")
        def turn_off(
            context: typer.Context,
            target: str = typer.Argument(help="A resource UUID or name."),
            transition: float | None = typer.Option(
                None, "--transition", help="Fade duration in seconds."
            ),
        ) -> None:
            """Turn a light, room, or zone off."""
            _write_response(
                context,
                _run(
                    _control(namespace_name, "turn_off", target, transition=transition)
                ),
            )

        @command_app.command("toggle")
        def toggle(
            context: typer.Context,
            target: str = typer.Argument(help="A resource UUID or name."),
            transition: float | None = typer.Option(
                None, "--transition", help="Fade duration in seconds."
            ),
        ) -> None:
            """Toggle a light, room, or zone."""
            _write_response(
                context,
                _run(_control(namespace_name, "toggle", target, transition=transition)),
            )

        @command_app.command("brightness")
        def set_brightness(
            context: typer.Context,
            target: str = typer.Argument(help="A resource UUID or name."),
            percent: float = typer.Argument(help="Brightness from 0 to 100."),
            transition: float | None = typer.Option(
                None, "--transition", help="Fade duration in seconds."
            ),
        ) -> None:
            """Set brightness; zero turns the target off."""
            _write_response(
                context,
                _run(
                    _control(
                        namespace_name,
                        "set_brightness",
                        target,
                        percent,
                        transition=transition,
                    )
                ),
            )

        @command_app.command("color")
        def set_color(
            context: typer.Context,
            target: str = typer.Argument(help="A resource UUID or name."),
            hex_color: str = typer.Argument(help="A #rgb or #rrggbb colour."),
            brightness: float | None = typer.Option(
                None, "--brightness", "-b", help="Brightness in percent."
            ),
            transition: float | None = typer.Option(
                None, "--transition", help="Fade duration in seconds."
            ),
        ) -> None:
            """Set a colour from hexadecimal RGB."""
            _write_response(
                context,
                _run(
                    _control(
                        namespace_name,
                        "set_hex",
                        target,
                        hex_color,
                        brightness=brightness,
                        transition=transition,
                    )
                ),
            )

        @command_app.command("temperature")
        def set_temperature(
            context: typer.Context,
            target: str = typer.Argument(help="A resource UUID or name."),
            kelvin: int = typer.Argument(help="Colour temperature in kelvin."),
            brightness: float | None = typer.Option(
                None, "--brightness", "-b", help="Brightness in percent."
            ),
            transition: float | None = typer.Option(
                None, "--transition", help="Fade duration in seconds."
            ),
        ) -> None:
            """Set a colour temperature in kelvin."""
            _write_response(
                context,
                _run(
                    _control(
                        namespace_name,
                        "set_color_temperature",
                        target,
                        kelvin,
                        brightness=brightness,
                        transition=transition,
                    )
                ),
            )

        @command_app.command("identify")
        def identify(
            context: typer.Context,
            target: str = typer.Argument(help="A resource UUID or name."),
        ) -> None:
            """Make the target breathe so it can be identified."""
            _write_response(context, _run(_control(namespace_name, "identify", target)))

    add_control_commands(light_app, "lights")
    add_control_commands(room_app, "rooms")
    add_control_commands(zone_app, "zones")

else:
    app = None


def main(argv: list[str] | None = None) -> int:
    """Run the CLI, with a useful error when its optional extra is absent."""
    if app is None:
        _missing_cli_extra()
    app(args=argv, prog_name="hueify")
    return 0
