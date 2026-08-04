from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from hueify.errors import ResourceNotFoundError
from hueify.http import HttpClient
from hueify.models import (
    GroupedLight,
    HueApiResponse,
    Light,
    LightUpdate,
    ResourceIdentifier,
    ResourceType,
    Room,
    Scene,
    Zone,
)
from hueify.resources import RoomNamespace, ZoneNamespace

ROOM_ID = UUID("33333333-3333-3333-3333-333333333333")
ZONE_ID = UUID("55555555-5555-5555-5555-555555555555")
GROUPED_LIGHT_ID = UUID("44444444-4444-4444-4444-444444444444")
CEILING_ID = UUID("11111111-1111-1111-1111-111111111111")
CEILING_DEVICE_ID = UUID("22222222-2222-2222-2222-222222222222")
DESK_ID = UUID("66666666-6666-6666-6666-666666666666")
DESK_DEVICE_ID = UUID("77777777-7777-7777-7777-777777777777")
SCENE_ID = UUID("88888888-8888-8888-8888-888888888888")

ROOM = {
    "id": str(ROOM_ID),
    "type": "room",
    "metadata": {"name": "Office", "archetype": "office"},
    "children": [{"rid": str(CEILING_DEVICE_ID), "rtype": "device"}],
    "services": [{"rid": str(GROUPED_LIGHT_ID), "rtype": "grouped_light"}],
}

ZONE = {
    "id": str(ZONE_ID),
    "type": "zone",
    "metadata": {"name": "Desk area", "archetype": "computer"},
    "children": [{"rid": str(DESK_ID), "rtype": "light"}],
    "services": [{"rid": str(GROUPED_LIGHT_ID), "rtype": "grouped_light"}],
}

LIGHTS = [
    {
        "id": str(CEILING_ID),
        "type": "light",
        "owner": {"rid": str(CEILING_DEVICE_ID), "rtype": "device"},
        "metadata": {"name": "Ceiling"},
        "on": {"on": True},
    },
    {
        "id": str(DESK_ID),
        "type": "light",
        "owner": {"rid": str(DESK_DEVICE_ID), "rtype": "device"},
        "metadata": {"name": "Desk"},
        "on": {"on": False},
    },
]

SCENES = [
    {
        "id": str(SCENE_ID),
        "type": "scene",
        "metadata": {"name": "Focus"},
        "group": {"rid": str(ROOM_ID), "rtype": "room"},
    },
    {
        "id": "99999999-9999-9999-9999-999999999999",
        "type": "scene",
        "metadata": {"name": "Elsewhere"},
        "group": {"rid": str(ZONE_ID), "rtype": "zone"},
    },
]

GROUPED_LIGHT = {
    "id": str(GROUPED_LIGHT_ID),
    "type": "grouped_light",
    "owner": {"rid": str(ROOM_ID), "rtype": "room"},
    "on": {"on": True},
    "dimming": {"brightness": 80.0},
}


def bridge(**overrides: object) -> AsyncMock:
    responses: dict[str, object] = {
        "room": HueApiResponse[Room].model_validate({"data": [ROOM]}),
        f"room/{ROOM_ID}": HueApiResponse[Room].model_validate({"data": [ROOM]}),
        "zone": HueApiResponse[Zone].model_validate({"data": [ZONE]}),
        f"zone/{ZONE_ID}": HueApiResponse[Zone].model_validate({"data": [ZONE]}),
        "light": HueApiResponse[Light].model_validate({"data": LIGHTS}),
        "scene": HueApiResponse[Scene].model_validate({"data": SCENES}),
        f"grouped_light/{GROUPED_LIGHT_ID}": HueApiResponse[
            GroupedLight
        ].model_validate({"data": [GROUPED_LIGHT]}),
    }
    responses.update(overrides)

    client = AsyncMock(spec=HttpClient)
    client.get.side_effect = lambda endpoint, _adapter: responses[endpoint]
    client.put.return_value = HueApiResponse[ResourceIdentifier](
        data=[
            ResourceIdentifier(rid=GROUPED_LIGHT_ID, rtype=ResourceType.GROUPED_LIGHT)
        ]
    )
    return client


@pytest.mark.asyncio
async def test_room_commands_address_the_grouped_light_service() -> None:
    client = bridge()

    await RoomNamespace(client).turn_on(ROOM_ID, brightness=70)

    endpoint, update = client.put.await_args.args
    assert endpoint == f"grouped_light/{GROUPED_LIGHT_ID}"
    assert isinstance(update, LightUpdate)
    assert update.model_dump(mode="json", exclude_none=True) == {
        "on": {"on": True},
        "dimming": {"brightness": 70.0},
    }


@pytest.mark.asyncio
async def test_zone_commands_use_the_same_command_surface_as_rooms() -> None:
    client = bridge()

    await ZoneNamespace(client).set_color(ZONE_ID, "red")

    endpoint, _ = client.put.await_args.args
    assert endpoint == f"grouped_light/{GROUPED_LIGHT_ID}"


@pytest.mark.asyncio
async def test_room_reports_the_on_state_of_its_grouped_light() -> None:
    assert await RoomNamespace(bridge()).is_on(ROOM_ID) is True


@pytest.mark.asyncio
async def test_room_lights_resolve_through_the_devices_a_room_contains() -> None:
    room_lights = await RoomNamespace(bridge()).lights(ROOM_ID)

    assert [light.metadata.name for light in room_lights] == ["Ceiling"]


@pytest.mark.asyncio
async def test_zone_lights_resolve_through_the_light_services_it_references() -> None:
    zone_lights = await ZoneNamespace(bridge()).lights(ZONE_ID)

    assert [light.metadata.name for light in zone_lights] == ["Desk"]


@pytest.mark.asyncio
async def test_scenes_are_listed_per_group() -> None:
    room_scenes = await RoomNamespace(bridge()).scenes(ROOM_ID)
    zone_scenes = await ZoneNamespace(bridge()).scenes(ZONE_ID)

    assert [scene.metadata.name for scene in room_scenes] == ["Focus"]
    assert [scene.metadata.name for scene in zone_scenes] == ["Elsewhere"]


@pytest.mark.asyncio
async def test_group_without_a_grouped_light_service_reports_a_clear_error() -> None:
    without_service = HueApiResponse[Room].model_validate(
        {"data": [{**ROOM, "services": []}]}
    )
    client = bridge(**{f"room/{ROOM_ID}": without_service})

    with pytest.raises(ResourceNotFoundError, match="no grouped light service"):
        await RoomNamespace(client).turn_off(ROOM_ID)


@pytest.mark.asyncio
async def test_groups_are_found_by_their_user_visible_name() -> None:
    room = await RoomNamespace(bridge()).find("office")

    assert room.id == ROOM_ID
