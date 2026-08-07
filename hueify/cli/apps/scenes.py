import typer
from typer import Context

from hueify.cli.operations import activate_scene, list_scenes, run
from hueify.cli.output import write_resources, write_response

app = typer.Typer(help="Inspect and activate scenes.")


@app.command("list")
def list_scenes_command(context: Context) -> None:
    """List scenes visible to the configured bridge."""
    scenes = run(list_scenes())
    write_resources(context, scenes, title="Scenes")


@app.command("activate")
def activate_scene_command(
    context: Context,
    target: str = typer.Argument(help="A scene UUID or name."),
    brightness: float | None = typer.Option(
        None, "--brightness", "-b", help="Brightness in percent."
    ),
    transition: float | None = typer.Option(
        None, "--transition", help="Fade duration in seconds."
    ),
    dynamic: bool = typer.Option(
        False, "--dynamic", help="Start the scene's dynamic palette."
    ),
) -> None:
    """Activate a scene, optionally with a brightness or fade."""
    response = run(
        activate_scene(
            target,
            brightness=brightness,
            transition=transition,
            dynamic=dynamic,
        )
    )
    write_response(context, response)
