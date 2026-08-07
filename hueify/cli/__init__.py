import sys
from typing import TYPE_CHECKING, NoReturn

if TYPE_CHECKING:
    from typer import Typer

_CLI_EXTRA_MESSAGE = (
    "Install the command line interface with: pip install 'hueify[cli]'"
)


def _missing_cli_extra() -> NoReturn:
    print(_CLI_EXTRA_MESSAGE, file=sys.stderr)
    raise SystemExit(1)


app: "Typer | None"

try:
    from hueify.cli.app import app as cli_app
except ModuleNotFoundError as error:  # pragma: no cover - optional dependency path
    if error.name not in {"click", "rich", "shellingham", "typer"}:
        raise
    app = None
else:
    app = cli_app


def main(argv: list[str] | None = None) -> int:
    """Run the CLI, with a useful error when its optional extra is absent."""
    if app is None:
        _missing_cli_extra()
    app(args=argv, prog_name="hueify")
    return 0


__all__ = ["app", "main"]
