from unittest.mock import AsyncMock, patch

import pytest

from hueify.credentials import HueBridgeCredentials
from hueify.onboarding.discovery import DiscoveredBridge
from hueify.onboarding.registration import RegisteredApp
from hueify.onboarding.setup import _run_setup, _select_bridge, setup

BRIDGE_A = DiscoveredBridge(id="a1", internalipaddress="192.168.1.10")
BRIDGE_B = DiscoveredBridge(id="b2", internalipaddress="192.168.1.20")
APP_KEY = "the-app-key-that-is-long-enough"
CLIENT_KEY = "0123456789abcdef0123456789abcdef"
REGISTERED_APP = RegisteredApp(app_key=APP_KEY, client_key=CLIENT_KEY)


def test_select_bridge_auto_selects_the_only_bridge_without_prompting() -> None:
    with patch("builtins.input") as user_input:
        selected = _select_bridge([BRIDGE_A])

    user_input.assert_not_called()
    assert selected is BRIDGE_A


def test_select_bridge_reprompts_on_invalid_choices() -> None:
    with patch("builtins.input", side_effect=["abc", "5", "2"]) as user_input:
        selected = _select_bridge([BRIDGE_A, BRIDGE_B])

    assert selected is BRIDGE_B
    assert user_input.call_count == 3


@pytest.mark.asyncio
async def test_run_setup_returns_the_discovered_and_registered_credentials() -> None:
    with (
        patch(
            "hueify.onboarding.setup.discover_bridges",
            new_callable=AsyncMock,
            return_value=[BRIDGE_A],
        ) as discover,
        patch(
            "hueify.onboarding.setup.register_app_key",
            new_callable=AsyncMock,
            return_value=REGISTERED_APP,
        ) as register,
        patch("builtins.input"),
    ):
        credentials = await _run_setup()

    discover.assert_awaited_once()
    register.assert_awaited_once_with(BRIDGE_A.internalipaddress)
    assert credentials.hue_bridge_ip == BRIDGE_A.internalipaddress
    assert credentials.hue_app_key == APP_KEY
    assert credentials.hue_client_key == CLIENT_KEY


@pytest.mark.asyncio
async def test_run_setup_writes_nothing_and_prints_the_variables(capsys) -> None:
    with (
        patch(
            "hueify.onboarding.setup.discover_bridges",
            new_callable=AsyncMock,
            return_value=[BRIDGE_A],
        ),
        patch(
            "hueify.onboarding.setup.register_app_key",
            new_callable=AsyncMock,
            return_value=REGISTERED_APP,
        ),
        patch("builtins.input"),
        patch("pathlib.Path.write_text") as write_text,
    ):
        await _run_setup()

    write_text.assert_not_called()
    printed = capsys.readouterr().out
    assert f"HUE_BRIDGE_IP={BRIDGE_A.internalipaddress}" in printed
    assert f"HUE_APP_KEY={APP_KEY}" in printed
    assert f"HUE_CLIENT_KEY={CLIENT_KEY}" in printed


def test_setup_runs_run_setup_to_completion_and_passes_the_result_through() -> None:
    credentials = HueBridgeCredentials(
        hue_bridge_ip=BRIDGE_A.internalipaddress, hue_app_key=APP_KEY
    )

    with patch(
        "hueify.onboarding.setup._run_setup",
        new_callable=AsyncMock,
        return_value=credentials,
    ) as run_setup:
        assert setup() is credentials

    run_setup.assert_awaited_once()
