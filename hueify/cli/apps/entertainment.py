import typer
from typer import Context

from hueify.cli.operations import (
    list_entertainment_areas,
    run,
    start_entertainment_area,
    stop_entertainment_area,
)
from hueify.cli.output import write_resources, write_response

app = typer.Typer(help="Inspect entertainment areas.")


@app.command("list")
def list_entertainment_areas_command(context: Context) -> None:
    """List entertainment areas and whether they are streaming."""
    areas = run(list_entertainment_areas())
    write_resources(context, areas, title="Entertainment areas")


@app.command("start")
def start_entertainment_area_command(
    context: Context,
    target: str = typer.Argument(help="An entertainment-area UUID or name."),
) -> None:
    """Take an entertainment area over for a streaming client."""
    response = run(start_entertainment_area(target))
    write_response(context, response)


@app.command("stop")
def stop_entertainment_area_command(
    context: Context,
    target: str = typer.Argument(help="An entertainment-area UUID or name."),
) -> None:
    """Release an entertainment area held by this application."""
    response = run(stop_entertainment_area(target))
    write_response(context, response)
