from uuid import uuid4

from hueify.models import (
    GroupedLight,
    HueApiResponse,
    Light,
    LightEvent,
    ResourceType,
    Room,
    Scene,
    Zone,
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
