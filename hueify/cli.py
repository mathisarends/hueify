"""The optional, shell-friendly ``hueify`` command line interface."""

import json
import sys
from dataclasses import dataclass
from importlib.metadata import version
from typing import Any, NoReturn

try:
    import typer
except ImportError:  # pragma: no cover - exercised without the optional extra
    typer = None


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

else:
    app = None


def main(argv: list[str] | None = None) -> int:
    """Run the CLI, with a useful error when its optional extra is absent."""
    if app is None:
        _missing_cli_extra()
    app(args=argv, prog_name="hueify")
    return 0
