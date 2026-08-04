try:
    import typer
except ImportError as e:
    raise ImportError(
        "CLI support requires 'typer'. Install with: pip install hueify[cli]"
    ) from e

from hueify.cli.setup import setup_command

app = typer.Typer(
    name="hueify",
    help="Onboard your Philips Hue Bridge.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)


@app.command("setup")
def setup() -> None:
    """Interactive onboarding: discover bridge and register an app key."""
    setup_command()


def main() -> None:
    app()
