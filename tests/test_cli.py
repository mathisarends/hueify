import pytest

typer = pytest.importorskip("typer")
pytest.importorskip("rich")

from typer.testing import CliRunner

from hueify.cli.server import app


def test_missing_credentials_show_setup_hint(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config_path = tmp_path / "missing-config.toml"
    runner = CliRunner()

    result = runner.invoke(
        app,
        ["lights", "list"],
        env={
            "HUEIFY_CONFIG_FILE": str(config_path),
            "HUE_BRIDGE_IP": None,
            "HUE_APP_KEY": None,
        },
    )

    assert result.exit_code == 1
    assert "Missing Hue credentials." in result.output
    assert "hueify setup" in result.output
    assert "--bridge-ip" in result.output
    assert "--app-key" in result.output
    assert "ValidationError" not in result.output


def test_invalid_credentials_do_not_show_setup_hint(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        app,
        ["--bridge-ip", "192.168.1.1", "--app-key", "short", "lights", "list"],
        env={
            "HUEIFY_CONFIG_FILE": str(tmp_path / "missing-config.toml"),
            "HUE_BRIDGE_IP": None,
            "HUE_APP_KEY": None,
        },
    )

    assert result.exit_code == 1
    assert "Invalid Hue credentials:" in result.output
    assert "hueify setup" not in result.output
