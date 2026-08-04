import pytest

pytest.importorskip("typer")
pytest.importorskip("rich")

from typer.testing import CliRunner

from hueify.cli.server import app


def test_setup_is_the_only_command():
    runner = CliRunner()

    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "setup" in result.output
    for removed in ("lights", "rooms", "zones"):
        assert removed not in result.output
