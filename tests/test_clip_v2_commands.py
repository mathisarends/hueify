import json
from pathlib import Path
from uuid import UUID

import pytest
from pydantic import ValidationError

from hueify import models as m

RESOURCE_ID = UUID("00000000-0000-0000-0000-000000000001")
OWNER_ID = UUID("00000000-0000-0000-0000-000000000002")
CONTRACT = json.loads(
    (Path(__file__).parent / "fixtures/clip_v2_contract.json").read_text(
        encoding="utf-8"
    )
)
KINDS = [item["resource_type"] for item in CONTRACT["resources"]]


def write_response(kind: str) -> dict:
    return {"data": [{"rid": str(RESOURCE_ID), "rtype": kind}], "errors": []}


COMMAND_CASES = [
    (
        "devices",
        "rename",
        ["Desk sensor"],
        {},
        "device",
        {"metadata": {"name": "Desk sensor"}},
    ),
    ("devices", "identify", [], {}, "device", {"identify": {"action": "identify"}}),
    (
        "devices",
        "set_usertest",
        [False],
        {},
        "device",
        {"usertest": {"usertest": False}},
    ),
    ("motions", "enable", [], {}, "motion", {"enabled": True}),
    ("motions", "disable", [], {}, "motion", {"enabled": False}),
    (
        "motions",
        "set_sensitivity",
        [0],
        {},
        "motion",
        {"sensitivity": {"sensitivity": 0}},
    ),
    ("temperatures", "disable", [], {}, "temperature", {"enabled": False}),
    ("camera_motions", "enable", [], {}, "camera_motion", {"enabled": True}),
    ("contacts", "enable", [], {}, "contact", {"enabled": True}),
    ("light_levels", "enable", [], {}, "light_level", {"enabled": True}),
    (
        "convenience_area_motions",
        "enable",
        [],
        {},
        "convenience_area_motion",
        {"enabled": True},
    ),
    (
        "security_area_motions",
        "disable",
        [],
        {},
        "security_area_motion",
        {"enabled": False},
    ),
    (
        "motion_area_configurations",
        "enable",
        [],
        {},
        "motion_area_configuration",
        {"enabled": True},
    ),
    (
        "device_software_updates",
        "install",
        [],
        {},
        "device_software_update",
        {"install": {"install_state": "install"}},
    ),
    (
        "zigbee_device_discovery",
        "search",
        [],
        {},
        "zigbee_device_discovery",
        {"action": {"action_type": "search"}},
    ),
    (
        "geofence_clients",
        "set_at_home",
        [False],
        {},
        "geofence_client",
        {"is_at_home": False},
    ),
    ("homekit", "reset", [], {}, "homekit", {"action": "homekit_reset"}),
    ("matter", "reset", [], {}, "matter", {"action": {"action_type": "matter_reset"}}),
    ("behavior_instances", "disable", [], {}, "behavior_instance", {"enabled": False}),
    (
        "smart_scenes",
        "activate",
        [],
        {},
        "smart_scene",
        {"recall": {"action": "activate"}},
    ),
    (
        "smart_scenes",
        "deactivate",
        [],
        {},
        "smart_scene",
        {"recall": {"action": "deactivate"}},
    ),
    (
        "grouped_lights",
        "set_brightness",
        [40],
        {},
        "grouped_light",
        {"on": {"on": True}, "dimming": {"brightness": 40}},
    ),
    (
        "lights",
        "set_effect",
        ["cosmos"],
        {"speed": 0},
        "light",
        {
            "on": {"on": True},
            "effects_v2": {"action": {"effect": "cosmos", "parameters": {"speed": 0}}},
        },
    ),
    (
        "lights",
        "set_effect",
        ["candle"],
        {"kelvin": 2700},
        "light",
        {
            "on": {"on": True},
            "effects_v2": {
                "action": {
                    "effect": "candle",
                    "parameters": {"color_temperature": {"mirek": 370}},
                }
            },
        },
    ),
    (
        "lights",
        "stop_effect",
        [],
        {},
        "light",
        {"effects_v2": {"action": {"effect": "no_effect"}}},
    ),
    (
        "lights",
        "set_timed_effect",
        ["sunrise"],
        {"duration": 30},
        "light",
        {"on": {"on": True}, "timed_effects": {"effect": "sunrise", "duration": 30000}},
    ),
    (
        "lights",
        "set_powerup_preset",
        ["last_on_state"],
        {},
        "light",
        {"powerup": {"preset": "last_on_state"}},
    ),
    ("lights", "stop_dimming", [], {}, "light", {"dimming_delta": {"action": "stop"}}),
    (
        "lights",
        "warmer",
        [20],
        {},
        "light",
        {"color_temperature_delta": {"action": "up", "mirek_delta": 20}},
    ),
    (
        "grouped_lights",
        "cooler",
        [30],
        {},
        "grouped_light",
        {"color_temperature_delta": {"action": "down", "mirek_delta": 30}},
    ),
    (
        "lights",
        "stop_color_temperature",
        [],
        {},
        "light",
        {"color_temperature_delta": {"action": "stop"}},
    ),
    (
        "lights",
        "signal",
        ["no_signal"],
        {},
        "light",
        {"signaling": {"signal": "no_signal"}},
    ),
    (
        "grouped_lights",
        "signal",
        ["on_off"],
        {"duration": 2},
        "grouped_light",
        {"signaling": {"signal": "on_off", "duration": 2000}},
    ),
]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("namespace", "command", "args", "kwargs", "kind", "payload"),
    COMMAND_CASES,
    ids=[f"{row[0]}.{row[1]}-{index}" for index, row in enumerate(COMMAND_CASES)],
)
async def test_commands_send_exact_bridge_payloads(
    bridge,
    namespace: str,
    command: str,
    args: list,
    kwargs: dict,
    kind: str,
    payload: dict,
) -> None:
    hue, requests, responses = bridge
    responses.append(write_response(kind))
    result = await getattr(getattr(hue, namespace), command)(
        RESOURCE_ID, *args, **kwargs
    )
    assert requests[0].method == "PUT"
    assert requests[0].url.path == f"/clip/v2/resource/{kind}/{RESOURCE_ID}"
    assert json.loads(requests[0].content) == payload
    assert result.data[0].rid == RESOURCE_ID


@pytest.mark.asyncio
async def test_signaling_uses_singular_color_with_wrapped_xy_values(bridge) -> None:
    hue, requests, responses = bridge
    responses.append(write_response("light"))
    await hue.lights.signal(
        RESOURCE_ID,
        "alternating",
        duration=3,
        colors=[m.ColorXY(x=0.5, y=0.4), m.ColorXY(x=0.2, y=0.3)],
    )
    assert json.loads(requests[0].content) == {
        "signaling": {
            "signal": "alternating",
            "duration": 3000,
            "color": [{"xy": {"x": 0.5, "y": 0.4}}, {"xy": {"x": 0.2, "y": 0.3}}],
        }
    }


@pytest.mark.asyncio
async def test_gradient_preserves_order_and_has_no_read_only_capabilities(
    bridge,
) -> None:
    hue, requests, responses = bridge
    responses.append(write_response("light"))
    await hue.lights.set_gradient(
        RESOURCE_ID,
        [m.ColorXY(x=0.5, y=0.4), m.ColorXY(x=0.2, y=0.3)],
        mode="interpolated_palette",
    )
    assert json.loads(requests[0].content) == {
        "on": {"on": True},
        "gradient": {
            "mode": "interpolated_palette",
            "points": [
                {"color": {"xy": {"x": 0.5, "y": 0.4}}},
                {"color": {"xy": {"x": 0.2, "y": 0.3}}},
            ],
        },
    }
    assert m.GradientUpdate(mode="interpolated_palette").model_dump(
        exclude_none=True
    ) == {"mode": "interpolated_palette"}


@pytest.mark.asyncio
@pytest.mark.parametrize("kind", ["room", "zone", "scene", "smart_scene"])
async def test_creation_posts_complete_payloads_with_validated_required_fields(
    bridge, kind: str
) -> None:
    hue, requests, responses = bridge
    responses.append(write_response(kind))
    if kind in {"room", "zone"}:
        data = m.GroupCreate(
            metadata=m.GroupMetadata(name="Office", archetype="office")
        )
        expected = {
            "metadata": {"name": "Office", "archetype": "office"},
            "children": [],
        }
    elif kind == "scene":
        data = m.SceneCreate(
            metadata=m.SceneMetadata(name="Focus"),
            group=m.ResourceReference(rid=OWNER_ID, rtype="room"),
            actions=[],
        )
        expected = {
            "metadata": {"name": "Focus"},
            "group": {"rid": str(OWNER_ID), "rtype": "room"},
            "actions": [],
        }
    else:
        data = m.SmartSceneCreate(
            metadata=m.MetadataUpdate(name="Day"),
            group=m.ResourceReference(rid=OWNER_ID, rtype="zone"),
            week_timeslots=[
                m.SmartSceneDay(
                    recurrence=["monday"],
                    timeslots=[
                        m.SmartSceneTimeslot(
                            target=m.ResourceReference(rid=RESOURCE_ID, rtype="scene"),
                            start_time=m.SmartSceneStartTime(
                                kind="time", time=m.SmartSceneTime(hour=7, minute=30)
                            ),
                        )
                    ],
                )
            ],
        )
        expected = {
            "metadata": {"name": "Day"},
            "group": {"rid": str(OWNER_ID), "rtype": "zone"},
            "week_timeslots": [
                {
                    "recurrence": ["monday"],
                    "timeslots": [
                        {
                            "target": {"rid": str(RESOURCE_ID), "rtype": "scene"},
                            "start_time": {
                                "kind": "time",
                                "time": {"hour": 7, "minute": 30, "second": 0},
                            },
                        }
                    ],
                }
            ],
        }
    await hue.resources[kind].create(data)
    assert requests[0].method == "POST"
    assert requests[0].url.path == f"/clip/v2/resource/{kind}"
    assert json.loads(requests[0].content) == expected


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("namespace", "command", "args", "kwargs"),
    [
        ("motions", "set_sensitivity", [-1], {}),
        ("lights", "set_effect", ["candle"], {"speed": 1.1}),
        (
            "lights",
            "set_effect",
            ["candle"],
            {"color": m.ColorXY(x=0.5, y=0.4), "kelvin": 2700},
        ),
        ("lights", "set_gradient", [[m.ColorXY(x=0.5, y=0.4)]], {}),
        ("lights", "set_gradient", [[m.ColorXY(x=0.5, y=0.4)] * 6], {}),
        (
            "lights",
            "signal",
            ["alternating"],
            {"duration": 1, "colors": [m.ColorXY(x=0.5, y=0.4)]},
        ),
        ("lights", "signal", ["on_off"], {}),
        ("lights", "signal", ["unknown_signal"], {}),
        ("lights", "warmer", [348], {}),
        ("lights", "set_timed_effect", ["sunrise"], {"duration": -1}),
        ("lights", "set_timed_effect", ["sunrise"], {"duration": 21601}),
        ("lights", "set_powerup_preset", ["custom"], {}),
    ],
)
async def test_invalid_commands_fail_before_network_io(
    bridge, namespace: str, command: str, args: list, kwargs: dict
) -> None:
    hue, requests, _ = bridge
    with pytest.raises(ValueError):
        await getattr(getattr(hue, namespace), command)(RESOURCE_ID, *args, **kwargs)
    assert not requests


@pytest.mark.asyncio
async def test_using_a_snapshot_as_an_update_is_rejected(bridge) -> None:
    hue, requests, _ = bridge
    with pytest.raises(TypeError, match="DeviceUpdate"):
        await hue.devices.update(RESOURCE_ID, m.Device(id=RESOURCE_ID))
    assert not requests


@pytest.mark.asyncio
@pytest.mark.parametrize("namespace", ["lights", "grouped_lights", "rooms", "zones"])
async def test_apply_rejects_snapshots_before_resolving_or_writing(
    bridge, namespace: str
) -> None:
    hue, requests, _ = bridge
    with pytest.raises(TypeError, match="LightUpdate"):
        await getattr(hue, namespace).apply(RESOURCE_ID, m.Device(id=RESOURCE_ID))
    assert not requests


@pytest.mark.asyncio
async def test_scene_recall_rejects_snapshot_payloads_before_writing(bridge) -> None:
    hue, requests, _ = bridge
    with pytest.raises(TypeError, match="SceneRecallRequest"):
        await hue.scenes.recall(RESOURCE_ID, m.SceneUpdate())
    assert not requests


@pytest.mark.parametrize("kind", [*KINDS, "switch_input_configuration"])
def test_every_namespace_has_a_typed_partial_event(kind: str) -> None:
    payload = {"id": str(RESOURCE_ID), "type": kind, "future_change": 1}
    event = m.HueEventMessage.model_validate({"data": [payload]}).data[0]
    assert type(event) is not m.HueEvent
    assert event.type == kind
    assert event.model_dump(mode="json", exclude_none=True) == payload


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "kind",
    [
        "light",
        "grouped_light",
        "room",
        "zone",
        "scene",
        "motion",
        "bridge",
        "entertainment_configuration",
    ],
)
async def test_events_are_read_changes_and_cannot_be_sent_as_updates(
    bridge, kind: str
) -> None:
    hue, requests, _ = bridge
    event = m.HueEventMessage.model_validate(
        {"data": [{"id": str(RESOURCE_ID), "type": kind}]}
    ).data[0]
    with pytest.raises(TypeError, match="update expects"):
        await hue.resources[kind].update(RESOURCE_ID, event)
    assert not requests


def test_sensor_reports_prefer_current_reports_and_ignore_invalid_legacy_values() -> (
    None
):
    motion = m.Motion(
        id=RESOURCE_ID,
        motion=m.MotionState(
            motion=False,
            motion_valid=False,
            motion_report=m.MotionReport(motion=True, changed="2026-10-04T12:00:00Z"),
        ),
    )
    assert motion.detected is True
    assert m.MotionState(motion=True, motion_valid=False).detected is None
    temperature = m.Temperature(
        id=RESOURCE_ID,
        temperature=m.TemperatureState(
            temperature=0,
            temperature_valid=False,
            temperature_report=m.TemperatureReport(temperature=23.5),
        ),
    )
    assert temperature.celsius == 23.5
    assert (
        m.Temperature(
            id=RESOURCE_ID,
            temperature=m.TemperatureState(temperature=0, temperature_valid=False),
        ).celsius
        is None
    )
    light = m.LightLevel(
        id=RESOURCE_ID,
        light=m.LightLevelState(
            light_level=1,
            light_level_valid=False,
            light_level_report=m.LightLevelReport(light_level=20001),
        ),
    )
    assert light.lux == pytest.approx(100)
    assert m.LightLevelState(light_level=1, light_level_valid=False).lux is None


@pytest.mark.parametrize(
    "values",
    [
        {"kind": "time"},
        {"kind": "sunset", "time": {"hour": 7, "minute": 0}},
        {"kind": "time", "time": {"hour": 24, "minute": 0}},
    ],
)
def test_smart_scene_times_validate_clock_and_sunset_variants(values: dict) -> None:
    with pytest.raises(ValidationError):
        m.SmartSceneStartTime.model_validate(values)


def test_palette_matches_bridge_shapes_for_dimming_and_effects() -> None:
    palette = m.ScenePalette.model_validate(
        {
            "dimming": [{"brightness": 50}],
            "effects": [{"effect": "candle"}],
            "color": [
                {"color": {"xy": {"x": 0.5, "y": 0.4}}, "dimming": {"brightness": 60}}
            ],
        }
    )
    assert palette.dimming[0].brightness == 50
    assert palette.effects[0].effect == "candle"
    assert palette.color[0].dimming.brightness == 60


@pytest.mark.parametrize(
    ("kind", "patch"),
    [
        ("device", {"usertest": {"status": "changing"}}),
        ("motion", {"sensitivity": {"status": "changing"}}),
        ("motion", {"motion": {"motion_report": {"changed": "2026-10-04T12:00:00Z"}}}),
        ("button", {"button": {"button_report": {"updated": "2026-10-04T12:00:00Z"}}}),
        (
            "relative_rotary",
            {"relative_rotary": {"rotary_report": {"rotation": {"steps": 1}}}},
        ),
        ("smart_scene", {"active_timeslot": {"timeslot_id": 1}}),
        (
            "light",
            {
                "effects_v2": {
                    "status": {"effect": "candle", "parameters": {"speed": 0.5}}
                }
            },
        ),
        ("light", {"gradient": {"points_capable": 3}}),
        ("light", {"powerup": {"configured": True}}),
        ("light", {"signaling": {"signal_values": ["on_off"]}}),
        ("light", {"dimming": {"min_dim_level": 0.2}}),
        ("grouped_light", {"dimming": {"min_dim_level": 0.2}}),
    ],
)
def test_nested_partial_events_do_not_require_snapshot_fields(
    kind: str, patch: dict
) -> None:
    event = m.HueEventMessage.model_validate(
        {"data": [{"id": str(RESOURCE_ID), "type": kind, **patch}]}
    ).data[0]
    assert type(event) is not m.HueEvent
    assert set(patch) <= event.model_fields_set


@pytest.mark.parametrize("points", [None, []])
def test_gradient_events_distinguish_missing_points_from_an_empty_palette(
    points: list | None,
) -> None:
    gradient = {"mode": "interpolated_palette"}
    if points is not None:
        gradient["points"] = points
    event = m.LightEvent(id=RESOURCE_ID, gradient=gradient)

    assert event.gradient.points == points
    assert event.gradient.model_dump(exclude_unset=True) == gradient


@pytest.mark.parametrize(
    "event, field, expected",
    [
        (m.MotionEvent(id=RESOURCE_ID, motion={"motion": True}), "detected", True),
        (
            m.TemperatureEvent(id=RESOURCE_ID, temperature={"temperature": 21.5}),
            "celsius",
            21.5,
        ),
        (m.LightLevelEvent(id=RESOURCE_ID, light={"light_level": 20001}), "lux", 100),
    ],
)
def test_partial_sensor_events_keep_the_snapshot_accessors(
    event: m.HueEvent, field: str, expected: float | bool
) -> None:
    assert getattr(event, field) == pytest.approx(expected)


@pytest.mark.asyncio
async def test_stopping_a_timed_effect_has_no_duration_or_on_state(bridge) -> None:
    hue, requests, responses = bridge
    responses.append(write_response("light"))
    await hue.lights.stop_timed_effect(RESOURCE_ID)
    assert json.loads(requests[0].content) == {"timed_effects": {"effect": "no_effect"}}


@pytest.mark.asyncio
@pytest.mark.parametrize("kind", ["room", "zone", "scene", "smart_scene"])
async def test_update_requests_cannot_be_used_for_creation(bridge, kind: str) -> None:
    hue, requests, _ = bridge
    update = {
        "room": m.GroupUpdate,
        "zone": m.GroupUpdate,
        "scene": m.SceneUpdate,
        "smart_scene": m.SmartSceneUpdate,
    }[kind]()
    with pytest.raises(TypeError):
        await hue.resources[kind].create(update)
    assert not requests
