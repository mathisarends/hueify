from unittest.mock import AsyncMock, patch

import pytest

from hueify.onboarding.discovery import DiscoveredBridge
from hueify.onboarding.setup import _run_setup, _select_bridge, setup

BRIDGE_A = DiscoveredBridge(id="a1", internalipaddress="192.168.1.10")
BRIDGE_B = DiscoveredBridge(id="b2", internalipaddress="192.168.1.20")


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
async def test_run_setup_wires_discovery_registration_and_credential_saving() -> None:
    with (
        patch(
            "hueify.onboarding.setup.discover_bridges",
            new_callable=AsyncMock,
            return_value=[BRIDGE_A],
        ) as discover,
        patch(
            "hueify.onboarding.setup.register_app_key",
            new_callable=AsyncMock,
            return_value="the-app-key",
        ) as register,
        patch(
            "hueify.onboarding.setup.save_credentials_config",
            return_value="/config/path",
        ) as save,
        patch("builtins.input"),
    ):
        await _run_setup()

    discover.assert_awaited_once()
    register.assert_awaited_once_with(BRIDGE_A.internalipaddress)
    save.assert_called_once_with(BRIDGE_A.internalipaddress, "the-app-key")


def test_setup_runs_run_setup_to_completion() -> None:
    with patch(
        "hueify.onboarding.setup._run_setup", new_callable=AsyncMock
    ) as run_setup:
        setup()

    run_setup.assert_awaited_once()
