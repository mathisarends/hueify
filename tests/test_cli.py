from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

from typer.testing import CliRunner

from hueify.cli import app

runner = CliRunner()


def test_setup_command_runs_the_interactive_onboarding() -> None:
    with patch("hueify.onboarding.setup.setup") as setup:
        result = runner.invoke(app, ["setup"])

    assert result.exit_code == 0
    setup.assert_called_once_with()


def test_bare_invocation_prints_contextual_help() -> None:
    result = runner.invoke(app, [])

    assert result.exit_code == 2
    assert "setup" in result.output
    assert "--json" in result.output


def test_the_global_output_modes_are_mutually_exclusive() -> None:
    result = runner.invoke(app, ["--json", "--plain", "version-info"])

    assert result.exit_code == 2
    assert "either --json or --plain" in result.output


def test_version_info_has_human_plain_and_json_forms() -> None:
    plain = runner.invoke(app, ["--plain", "version-info"])
    structured = runner.invoke(app, ["--json", "version-info"])

    assert plain.exit_code == structured.exit_code == 0
    assert plain.output.strip()
    assert '"version"' in structured.output


def test_light_list_uses_the_hueify_api_and_writes_stable_plain_output() -> None:
    light = SimpleNamespace(
        id=UUID("a1b2c3d4-1111-2222-3333-444455556666"),
        name="Desk",
        is_on=True,
    )
    hue = MagicMock()
    hue.__aenter__ = AsyncMock(return_value=hue)
    hue.__aexit__ = AsyncMock(return_value=None)
    hue.lights.list = AsyncMock(return_value=SimpleNamespace(data=[light]))

    with patch("hueify.cli.Hueify", return_value=hue):
        result = runner.invoke(app, ["--plain", "light", "list"])

    assert result.exit_code == 0
    assert result.output == f"{light.id}\tDesk\ton\n"
    hue.lights.list.assert_awaited_once_with()


def test_resource_list_json_preserves_the_full_model_shape() -> None:
    light = MagicMock()
    light.model_dump.return_value = {"id": "light-id", "metadata": {"name": "Desk"}}
    hue = MagicMock()
    hue.__aenter__ = AsyncMock(return_value=hue)
    hue.__aexit__ = AsyncMock(return_value=None)
    hue.lights.list = AsyncMock(return_value=SimpleNamespace(data=[light]))

    with patch("hueify.cli.Hueify", return_value=hue):
        result = runner.invoke(app, ["--json", "light", "list"])

    assert result.exit_code == 0
    assert '"light-id"' in result.output
    assert '"metadata"' in result.output
