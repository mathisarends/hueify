from uuid import uuid4

from hueify.models import HueApiResponse, Light, ResourceType


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
