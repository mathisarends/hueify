import typer
from typer import Context

from hueify.cli.operations import (
    ControlGroup,
    identify,
    run,
    set_brightness,
    set_color,
    set_temperature,
    toggle,
    turn_off,
    turn_on,
)
from hueify.cli.output import write_response


def add_control_commands(command_app: typer.Typer, group: ControlGroup) -> None:
    """Attach the common light-control vocabulary to one resource app."""

    @command_app.command("on")
    def turn_on_command(
        context: Context,
        target: str = typer.Argument(help="A resource UUID or name."),
        brightness: float | None = typer.Option(
            None, "--brightness", "-b", help="Brightness in percent."
        ),
        transition: float | None = typer.Option(
            None, "--transition", help="Fade duration in seconds."
        ),
    ) -> None:
        """Turn a light, room, or zone on."""
        response = run(
            turn_on(
                group,
                target,
                brightness=brightness,
                transition=transition,
            )
        )
        write_response(context, response)

    @command_app.command("off")
    def turn_off_command(
        context: Context,
        target: str = typer.Argument(help="A resource UUID or name."),
        transition: float | None = typer.Option(
            None, "--transition", help="Fade duration in seconds."
        ),
    ) -> None:
        """Turn a light, room, or zone off."""
        response = run(turn_off(group, target, transition=transition))
        write_response(context, response)

    @command_app.command("toggle")
    def toggle_command(
        context: Context,
        target: str = typer.Argument(help="A resource UUID or name."),
        transition: float | None = typer.Option(
            None, "--transition", help="Fade duration in seconds."
        ),
    ) -> None:
        """Toggle a light, room, or zone."""
        response = run(toggle(group, target, transition=transition))
        write_response(context, response)

    @command_app.command("brightness")
    def set_brightness_command(
        context: Context,
        target: str = typer.Argument(help="A resource UUID or name."),
        percent: float = typer.Argument(help="Brightness from 0 to 100."),
        transition: float | None = typer.Option(
            None, "--transition", help="Fade duration in seconds."
        ),
    ) -> None:
        """Set brightness; zero turns the target off."""
        response = run(set_brightness(group, target, percent, transition=transition))
        write_response(context, response)

    @command_app.command("color")
    def set_color_command(
        context: Context,
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
        response = run(
            set_color(
                group,
                target,
                hex_color,
                brightness=brightness,
                transition=transition,
            )
        )
        write_response(context, response)

    @command_app.command("temperature")
    def set_temperature_command(
        context: Context,
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
        response = run(
            set_temperature(
                group,
                target,
                kelvin,
                brightness=brightness,
                transition=transition,
            )
        )
        write_response(context, response)

    @command_app.command("identify")
    def identify_command(
        context: Context,
        target: str = typer.Argument(help="A resource UUID or name."),
    ) -> None:
        """Make the target breathe so it can be identified."""
        response = run(identify(group, target))
        write_response(context, response)
