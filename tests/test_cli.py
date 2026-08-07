from unittest.mock import patch

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
