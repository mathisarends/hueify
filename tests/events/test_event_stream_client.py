import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from hueify.credentials import HueBridgeCredentials
from hueify.models import LightEvent, ResourceType
from hueify.sse import EventStream


def make_events() -> EventStream:
    credentials = HueBridgeCredentials(
        hue_bridge_ip="192.168.1.1",
        hue_app_key="a" * 20,
    )
    return EventStream(credentials)


@pytest.mark.asyncio
async def test_on_can_be_used_as_typed_decorator() -> None:
    events = make_events()
    received: list[LightEvent] = []

    @events.on(ResourceType.LIGHT)
    async def on_light(event: LightEvent) -> None:
        received.append(event)

    event = LightEvent(
        id="00000000-0000-0000-0000-000000000001",
        type=ResourceType.LIGHT,
    )
    await events._bus.dispatch(event)

    assert received == [event]
    await events.close()


@pytest.mark.asyncio
async def test_connect_is_explicit_and_runs_in_background() -> None:
    events = make_events()
    listening = asyncio.Event()

    async def listen_forever() -> None:
        listening.set()
        await asyncio.Event().wait()

    with patch.object(
        events._stream, "connect", new=AsyncMock(side_effect=listen_forever)
    ) as connect:
        assert events.connected is False

        await events.connect()
        await listening.wait()

        assert events.connected is True
        connect.assert_awaited_once()
        await events.close()

    assert events.connected is False
