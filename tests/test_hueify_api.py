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
        "set_color",
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

    with patch.object(hue.events._stream, "connect", new_callable=AsyncMock) as connect:
        async with hue:
            assert hue.events.connected is False

    connect.assert_not_awaited()


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
    await hue.events._bus.dispatch(event)
    await hue.close()

    assert received == [event]
