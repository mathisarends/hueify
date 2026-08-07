import typer
from typer import Context

from hueify.cli.apps.controls import add_control_commands
from hueify.cli.operations import ControlGroup, list_lights, run
from hueify.cli.output import write_resources

app = typer.Typer(help="Inspect and control individual lights.")


@app.command("list")
def list_lights_command(context: Context) -> None:
    """List all lights visible to the configured bridge."""
    lights = run(list_lights())
    write_resources(context, lights, title="Lights")


add_control_commands(app, ControlGroup.LIGHTS)
