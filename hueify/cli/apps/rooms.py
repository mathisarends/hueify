import typer
from typer import Context

from hueify.cli.apps.controls import add_control_commands
from hueify.cli.operations import ControlGroup, list_rooms, run
from hueify.cli.output import write_resources

app = typer.Typer(help="Inspect and control rooms.")


@app.command("list")
def list_rooms_command(context: Context) -> None:
    """List all rooms visible to the configured bridge."""
    rooms = run(list_rooms())
    write_resources(context, rooms, title="Rooms")


add_control_commands(app, ControlGroup.ROOMS)
