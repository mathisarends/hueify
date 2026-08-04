from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from hueify.errors import ResourceNotFoundError
from hueify.http import HttpClient
from hueify.models import (
    HueApiResponse,
    Light,
    LightUpdate,
    ResourceIdentifier,
    ResourceType,
)
from hueify.resources import LightNamespace

LIGHT_ID = UUID("11111111-1111-1111-1111-111111111111")
DEVICE_ID = UUID("22222222-2222-2222-2222-222222222222")
ROOM_ID = UUID("33333333-3333-3333-3333-333333333333")
GROUPED_LIGHT_ID = UUID("44444444-4444-4444-4444-444444444444")


def light_payload(
    *, name: str = "Desk", on: bool = True, brightness: float = 40.0
) -> dict:
    return {
        "id": str(LIGHT_ID),
        "type": "light",
        "owner": {"rid": str(DEVICE_ID), "rtype": "device"},
        "metadata": {"name": name},
        "on": {"on": on},
        "dimming": {"brightness": brightness},
    }


@pytest.fixture
def client() -> AsyncMock:
    http_client = AsyncMock(spec=HttpClient)
    http_client.put.return_value = HueApiResponse[ResourceIdentifier](
        data=[ResourceIdentifier(rid=LIGHT_ID, rtype=ResourceType.LIGHT)]
    )
    return http_client


@pytest.fixture
def lights(client: AsyncMock) -> LightNamespace:
    client.get.return_value = HueApiResponse[Light].model_validate(
        {"data": [light_payload()]}
    )
    return LightNamespace(client)


def sent_update(client: AsyncMock) -> dict:
    _, update = client.put.await_args.args
    assert isinstance(update, LightUpdate)
    return update.model_dump(mode="json", exclude_none=True)


@pytest.mark.asyncio
async def test_turn_on_sends_only_the_on_state(
    lights: LightNamespace, client: AsyncMock
) -> None:
    await lights.turn_on(LIGHT_ID)

    assert client.put.await_args.args[0] == f"light/{LIGHT_ID}"
    assert sent_update(client) == {"on": {"on": True}}


@pytest.mark.asyncio
async def test_turn_on_accepts_brightness_and_transition_in_one_call(
    lights: LightNamespace, client: AsyncMock
) -> None:
    await lights.turn_on(LIGHT_ID, brightness=50, transition=1.5)

    assert sent_update(client) == {
        "on": {"on": True},
        "dimming": {"brightness": 50.0},
        "dynamics": {"duration": 1500},
    }


@pytest.mark.asyncio
async def test_turn_off_does_not_send_a_brightness(
    lights: LightNamespace, client: AsyncMock
) -> None:
    await lights.turn_off(LIGHT_ID)

    assert sent_update(client) == {"on": {"on": False}}


@pytest.mark.asyncio
async def test_toggle_inverts_the_current_on_state(
    lights: LightNamespace, client: AsyncMock
) -> None:
    await lights.toggle(LIGHT_ID)

    assert sent_update(client) == {"on": {"on": False}}


@pytest.mark.asyncio
async def test_set_brightness_also_switches_the_light_on(
    lights: LightNamespace, client: AsyncMock
) -> None:
    await lights.set_brightness(LIGHT_ID, 65)

    assert sent_update(client) == {"on": {"on": True}, "dimming": {"brightness": 65.0}}


@pytest.mark.asyncio
async def test_zero_brightness_turns_the_light_off(
    lights: LightNamespace, client: AsyncMock
) -> None:
    await lights.set_brightness(LIGHT_ID, 0)

    assert sent_update(client) == {"on": {"on": False}}


@pytest.mark.asyncio
async def test_brighten_uses_a_relative_delta_instead_of_reading_first(
    lights: LightNamespace, client: AsyncMock
) -> None:
    await lights.brighten(LIGHT_ID, by=15)

    assert sent_update(client) == {
        "dimming_delta": {"action": "up", "brightness_delta": 15.0}
    }
    client.get.assert_not_awaited()


@pytest.mark.asyncio
async def test_dim_steps_down_by_ten_percent_by_default(
    lights: LightNamespace, client: AsyncMock
) -> None:
    await lights.dim(LIGHT_ID)

    assert sent_update(client) == {
        "dimming_delta": {"action": "down", "brightness_delta": 10.0}
    }


@pytest.mark.asyncio
async def test_set_color_translates_a_hex_string_into_cie_xy(
    lights: LightNamespace, client: AsyncMock
) -> None:
    await lights.set_color(LIGHT_ID, "#ff8800")

    update = sent_update(client)
    assert update["on"] == {"on": True}
    assert set(update["color"]["xy"]) == {"x", "y"}


@pytest.mark.asyncio
async def test_set_color_temperature_translates_kelvin_into_mirek(
    lights: LightNamespace, client: AsyncMock
) -> None:
    await lights.set_color_temperature(LIGHT_ID, 2700)

    assert sent_update(client) == {
        "on": {"on": True},
        "color_temperature": {"mirek": 370},
    }


@pytest.mark.asyncio
async def test_set_state_sends_exactly_what_it_is_given(
    lights: LightNamespace, client: AsyncMock
) -> None:
    await lights.set_state(LIGHT_ID, brightness=30)

    assert sent_update(client) == {"dimming": {"brightness": 30.0}}


@pytest.mark.asyncio
async def test_color_and_color_temperature_are_mutually_exclusive(
    lights: LightNamespace,
) -> None:
    with pytest.raises(ValueError, match="either a color or a color temperature"):
        await lights.set_state(LIGHT_ID, color="red", kelvin=2700)


@pytest.mark.asyncio
async def test_kelvin_and_mirek_cannot_be_combined(lights: LightNamespace) -> None:
    with pytest.raises(ValueError, match="either kelvin or mirek"):
        await lights.set_state(LIGHT_ID, kelvin=2700, mirek=370)


@pytest.mark.asyncio
async def test_identify_sends_a_breathe_alert(
    lights: LightNamespace, client: AsyncMock
) -> None:
    await lights.identify(LIGHT_ID)

    assert sent_update(client) == {"alert": {"action": "breathe"}}


@pytest.mark.asyncio
async def test_negative_transitions_are_rejected(lights: LightNamespace) -> None:
    with pytest.raises(ValueError, match="cannot be negative"):
        await lights.turn_on(LIGHT_ID, transition=-1)


@pytest.mark.asyncio
async def test_unknown_light_id_raises_a_named_error(client: AsyncMock) -> None:
    client.get.return_value = HueApiResponse[Light]()

    with pytest.raises(ResourceNotFoundError, match="No light with ID"):
        await LightNamespace(client).get_one(LIGHT_ID)


@pytest.mark.asyncio
async def test_find_by_name_reports_the_known_names_when_nothing_matches(
    client: AsyncMock,
) -> None:
    client.get.return_value = HueApiResponse[Light].model_validate(
        {"data": [light_payload()]}
    )

    with pytest.raises(ResourceNotFoundError, match="Known names: Desk"):
        await LightNamespace(client).find_by_name("Couch")


@pytest.mark.asyncio
async def test_find_by_name_matches_a_name_case_insensitively(
    client: AsyncMock,
) -> None:
    client.get.return_value = HueApiResponse[Light].model_validate(
        {"data": [light_payload()]}
    )

    assert (await LightNamespace(client).find_by_name("  desk ")).id == LIGHT_ID


@pytest.mark.asyncio
async def test_find_by_name_fuzzy_matches_a_typo(client: AsyncMock) -> None:
    client.get.return_value = HueApiResponse[Light].model_validate(
        {"data": [light_payload()]}
    )

    result = await LightNamespace(client).find_by_name("Dsek")

    assert result.metadata.name == "Desk"


@pytest.mark.asyncio
async def test_find_by_name_reports_known_names_by_relevance(
    client: AsyncMock,
) -> None:
    client.get.return_value = HueApiResponse[Light].model_validate(
        {
            "data": [
                light_payload(name="Bedroom"),
                light_payload(name="Desk"),
                light_payload(name="Kitchen"),
            ]
        }
    )

    with pytest.raises(ResourceNotFoundError) as error:
        await LightNamespace(client).find_by_name("Ceiling")

    assert "Known names: Kitchen, Desk, Bedroom" in str(error.value)
