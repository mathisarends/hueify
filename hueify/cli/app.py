from importlib.metadata import version

import typer
from typer import Context

from hueify.cli.apps import (
    entertainment_app,
    light_app,
    room_app,
    scene_app,
    zone_app,
)
from hueify.cli.output import OutputOptions, print_json

app = typer.Typer(
    name="hueify",
    help="Control Philips Hue bridges from the command line.",
    no_args_is_help=True,
    rich_markup_mode="markdown",
)


@app.callback(invoke_without_command=True)
def callback(
    context: Context,
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
def version_info(context: Context) -> None:
    """Show the installed Hueify version in the selected output mode."""
    output = OutputOptions.from_context(context)
    installed_version = version("hueify")
    if output.json:
        print_json({"version": installed_version})
    elif output.plain:
        typer.echo(installed_version)
    else:
        typer.echo(f"Hueify {installed_version}")


app.add_typer(light_app, name="light")
app.add_typer(room_app, name="room")
app.add_typer(zone_app, name="zone")
app.add_typer(scene_app, name="scene")
app.add_typer(entertainment_app, name="entertainment")
