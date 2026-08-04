from unittest.mock import patch

from hueify.cli import main


def test_setup_command_runs_the_interactive_onboarding() -> None:
    with patch("hueify.cli.setup") as setup:
        exit_code = main(["setup"])

    setup.assert_called_once_with()
    assert exit_code == 0


def test_bare_invocation_prints_help_and_fails(capsys) -> None:
    exit_code = main([])

    assert exit_code == 1
    assert "setup" in capsys.readouterr().out
