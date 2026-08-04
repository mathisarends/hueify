import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from hueify import Hueify
from hueify.models import LightEvent, ResourceType
from hueify.resources import (
    LightNamespace,
    RoomNamespace,
    SceneNamespace,
    ZoneNamespace,
)

VALID_IP = "192.168.1.100"
VALID_APP_KEY = "a" * 40


async def _never_returns() -> None:
    """Stand in for the real stream, which runs until it is cancelled."""
    await asyncio.Event().wait()


def _patched_stream(hue: Hueify) -> AsyncMock:
    return patch.object(
        hue._events._stream,
        "connect",
        new_callable=AsyncMock,
        side_effect=_never_returns,
    )


@pytest.mark.asyncio
async def test_exposes_exactly_the_four_supported_resource_namespaces() -> None:
    hue = Hueify(bridge_ip=VALID_IP, app_key=VALID_APP_KEY)
    try:
        assert isinstance(hue.lights, LightNamespace)
        assert isinstance(hue.rooms, RoomNamespace)
        assert isinstance(hue.zones, ZoneNamespace)
        assert isinstance(hue.scenes, SceneNamespace)
        assert not hasattr(hue, "grouped_lights")
        assert not hasattr(hue, "geolocations")
    finally:
        await hue.close()


@pytest.mark.asyncio
async def test_lights_rooms_and_zones_share_one_command_surface() -> None:
    hue = Hueify(bridge_ip=VALID_IP, app_key=VALID_APP_KEY)
    commands = {
        "turn_on",
        "turn_off",
        "toggle",
        "is_on",
        "set_brightness",
        "brighten",
        "dim",
        "set_rgb",
        "set_hex",
        "set_color_temperature",
        "set_state",
        "identify",
        "apply",
    }
    try:
        for namespace in (hue.lights, hue.rooms, hue.zones):
            missing = {name for name in commands if not hasattr(namespace, name)}
            assert not missing, f"{namespace.resource_type} is missing {missing}"
    finally:
        await hue.close()


@pytest.mark.asyncio
async def test_context_manager_does_not_start_event_stream() -> None:
    hue = Hueify(bridge_ip=VALID_IP, app_key=VALID_APP_KEY)

    with _patched_stream(hue) as connect:
        async with hue:
            assert hue.events_connected is False

    connect.assert_not_awaited()


@pytest.mark.asyncio
async def test_start_events_connects_and_stop_events_disconnects() -> None:
    hue = Hueify(bridge_ip=VALID_IP, app_key=VALID_APP_KEY)

    with _patched_stream(hue):
        async with hue:
            await hue.start_events()
            assert hue.events_connected is True

            await hue.stop_events()
            assert hue.events_connected is False


@pytest.mark.asyncio
async def test_starting_events_twice_keeps_one_connection() -> None:
    hue = Hueify(bridge_ip=VALID_IP, app_key=VALID_APP_KEY)

    with _patched_stream(hue) as connect:
        async with hue:
            await hue.start_events()
            await hue.start_events()

    assert connect.await_count == 1


@pytest.mark.asyncio
async def test_leaving_the_context_manager_stops_a_started_stream() -> None:
    hue = Hueify(bridge_ip=VALID_IP, app_key=VALID_APP_KEY)

    with _patched_stream(hue):
        async with hue:
            await hue.start_events()

    assert hue.events_connected is False


@pytest.mark.asyncio
async def test_on_decorator_is_reexposed_on_hueify() -> None:
    hue = Hueify(bridge_ip=VALID_IP, app_key=VALID_APP_KEY)
    received: list[LightEvent] = []

    @hue.on(ResourceType.LIGHT)
    async def on_light(event: LightEvent) -> None:
        received.append(event)

    event = LightEvent(
        id="00000000-0000-0000-0000-000000000001",
        type=ResourceType.LIGHT,
    )
    await hue._events._bus.dispatch(event)
    await hue.close()

    assert received == [event]


@pytest.mark.asyncio
async def test_off_is_reexposed_on_hueify_and_stops_further_dispatches() -> None:
    hue = Hueify(bridge_ip=VALID_IP, app_key=VALID_APP_KEY)
    received: list[LightEvent] = []

    async def on_light(event: LightEvent) -> None:
        received.append(event)

    hue.on(ResourceType.LIGHT, on_light)
    hue.off(ResourceType.LIGHT, on_light)

    event = LightEvent(
        id="00000000-0000-0000-0000-000000000001",
        type=ResourceType.LIGHT,
    )
    await hue._events._bus.dispatch(event)
    await hue.close()

    assert received == []


@pytest.mark.asyncio
async def test_without_explicit_credentials_falls_back_to_settings(
    monkeypatch,
) -> None:
    monkeypatch.setenv("HUE_BRIDGE_IP", VALID_IP)
    monkeypatch.setenv("HUE_APP_KEY", VALID_APP_KEY)

    hue = Hueify()

    assert hue._credentials.hue_bridge_ip == VALID_IP
    assert hue._credentials.hue_app_key == VALID_APP_KEY
    await hue.close()
