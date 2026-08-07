import typer
from typer import Context

from hueify.cli.apps.controls import add_control_commands
from hueify.cli.operations import ControlGroup, list_zones, run
from hueify.cli.output import write_resources

app = typer.Typer(help="Inspect and control zones.")


@app.command("list")
def list_zones_command(context: Context) -> None:
    """List all zones visible to the configured bridge."""
    zones = run(list_zones())
    write_resources(context, zones, title="Zones")


add_control_commands(app, ControlGroup.ZONES)
