from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from hueify.models import (
    GroupedLight,
    HueApiResponse,
    HueEvent,
    HueEventMessage,
    Light,
    LightEvent,
    ResourceType,
    Room,
    RoomEvent,
    Scene,
    SceneEvent,
    Zone,
    ZoneEvent,
)


def test_light_response_is_typed_and_preserves_new_hue_fields() -> None:
    light_id = uuid4()
    owner_id = uuid4()
    response = HueApiResponse[Light].model_validate(
        {
            "errors": [],
            "data": [
                {
                    "id": str(light_id),
                    "type": "light",
                    "owner": {"rid": str(owner_id), "rtype": "device"},
                    "metadata": {"name": "Desk", "archetype": "table_shade"},
                    "on": {"on": True},
                    "dimming": {"brightness": 42.5},
                    "future_bridge_field": {"is_preserved": True},
                }
            ],
            "future_envelope_field": "also preserved",
        }
    )

    light = response.data[0]
    assert isinstance(light, Light)
    assert light.id == light_id
    assert light.type is ResourceType.LIGHT
    assert light.dimming is not None
    assert light.dimming.brightness == 42.5

    dumped = response.model_dump(mode="json")
    assert dumped["data"][0]["future_bridge_field"] == {"is_preserved": True}
    assert dumped["future_envelope_field"] == "also preserved"


def test_room_zone_and_scene_responses_use_concrete_models() -> None:
    room = (
        HueApiResponse[Room]
        .model_validate(
            {
                "data": [
                    {
                        "id": str(uuid4()),
                        "type": "room",
                        "metadata": {"name": "Office", "archetype": "office"},
                        "children": [],
                        "services": [],
                    }
                ]
            }
        )
        .data[0]
    )
    zone = (
        HueApiResponse[Zone]
        .model_validate(
            {
                "data": [
                    {
                        "id": str(uuid4()),
                        "type": "zone",
                        "metadata": {"name": "Upstairs", "archetype": "upstairs"},
                        "children": [],
                        "services": [],
                    }
                ]
            }
        )
        .data[0]
    )
    scene = (
        HueApiResponse[Scene]
        .model_validate(
            {
                "data": [
                    {
                        "id": str(uuid4()),
                        "type": "scene",
                        "metadata": {"name": "Focus"},
                        "group": {"rid": str(room.id), "rtype": "room"},
                    }
                ]
            }
        )
        .data[0]
    )

    assert room.type is ResourceType.ROOM
    assert zone.type is ResourceType.ZONE
    assert scene.type is ResourceType.SCENE

    assert room.name == "Office"
    assert zone.name == "Upstairs"
    assert scene.name == "Focus"


def _make_light(**overrides: object) -> Light:
    payload = {
        "id": str(uuid4()),
        "type": "light",
        "owner": {"rid": str(uuid4()), "rtype": "device"},
        "metadata": {"name": "Desk", "archetype": "table_shade"},
        "on": {"on": True},
    }
    payload.update(overrides)
    return Light.model_validate(payload)


def test_light_flattened_state_properties_reflect_nested_state() -> None:
    light = _make_light(
        on={"on": True},
        dimming={"brightness": 42.5},
        color_temperature={"mirek": 300},
        color={"xy": {"x": 0.5, "y": 0.4}},
    )

    assert light.name == "Desk"
    assert light.is_on is True
    assert light.brightness == 42.5
    assert light.mirek == 300
    assert light.xy is not None
    assert (light.xy.x, light.xy.y) == (0.5, 0.4)


def test_light_flattened_state_properties_are_none_when_sub_model_absent() -> None:
    light = _make_light(on={"on": False})

    assert light.is_on is False
    assert light.brightness is None
    assert light.mirek is None
    assert light.xy is None


def test_grouped_light_flattened_state_properties_are_none_by_default() -> None:
    grouped_light = GroupedLight.model_validate({"id": str(uuid4())})

    assert grouped_light.is_on is None
    assert grouped_light.brightness is None
    assert grouped_light.mirek is None
    assert grouped_light.xy is None

    grouped_light = GroupedLight.model_validate(
        {"id": str(uuid4()), "on": {"on": True}, "dimming": {"brightness": 10}}
    )

    assert grouped_light.is_on is True
    assert grouped_light.brightness == 10


def test_light_event_flattened_state_properties_reflect_partial_payload() -> None:
    event = LightEvent.model_validate(
        {
            "id": str(uuid4()),
            "type": "light",
            "dimming": {"brightness": 66},
        }
    )

    assert event.brightness == 66
    assert event.is_on is None
    assert event.mirek is None
    assert event.xy is None


def _make_message(*events: dict) -> dict:
    return {
        "creationtime": "2026-08-06T07:29:23Z",
        "id": str(uuid4()),
        "type": "update",
        "data": list(events),
    }


@pytest.mark.parametrize(
    ("resource_type", "expected_model"),
    [
        ("light", LightEvent),
        ("room", RoomEvent),
        ("zone", ZoneEvent),
        ("scene", SceneEvent),
    ],
)
def test_event_message_parses_each_resource_type_into_its_own_model(
    resource_type: str, expected_model: type[HueEvent]
) -> None:
    message = HueEventMessage.model_validate(
        _make_message({"id": str(uuid4()), "type": resource_type})
    )

    assert type(message.data[0]) is expected_model


def test_event_message_keeps_unmodelled_resource_types_generic() -> None:
    # The bridge reports far more resource types than hueify models, and new
    # ones arrive with firmware updates - they must not break the payload.
    message = HueEventMessage.model_validate(
        _make_message(
            {"id": str(uuid4()), "type": "light"},
            {"id": str(uuid4()), "type": "motion", "motion": {"motion": True}},
        )
    )

    light, motion = message.data
    assert isinstance(light, LightEvent)
    assert type(motion) is HueEvent
    assert motion.type == "motion"
    assert motion.model_extra == {"motion": {"motion": True}}


def test_event_message_parses_typed_fields_of_the_envelope() -> None:
    message = HueEventMessage.model_validate(_make_message())

    assert message.creationtime == datetime(2026, 8, 6, 7, 29, 23, tzinfo=UTC)
    assert message.data == []


def test_event_message_without_data_holds_no_events() -> None:
    message = HueEventMessage.model_validate({"type": "update"})

    assert message.data == []


def test_event_message_rejects_an_event_without_an_id() -> None:
    with pytest.raises(ValidationError):
        HueEventMessage.model_validate(_make_message({"type": "light"}))
