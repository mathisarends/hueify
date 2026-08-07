import pytest


@pytest.fixture
def without_stored_credentials(tmp_path, monkeypatch):
    """Hide the environment and any ``.env`` in the working directory."""
    monkeypatch.delenv("HUE_BRIDGE_IP", raising=False)
    monkeypatch.delenv("HUE_APP_KEY", raising=False)
    monkeypatch.delenv("HUE_CLIENT_KEY", raising=False)
    monkeypatch.chdir(tmp_path)
