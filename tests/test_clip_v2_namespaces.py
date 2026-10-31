"""HTTP contract tests against an independently pinned endpoint inventory."""

import json
from pathlib import Path
from uuid import UUID

import httpx
import pytest
from pydantic import TypeAdapter, ValidationError

from hueify import models as m
from hueify.errors import AmbiguousResourceError, ResourceNotFoundError

RESOURCE_ID = UUID("00000000-0000-0000-0000-000000000001")
OWNER_ID = UUID("00000000-0000-0000-0000-000000000002")
CONTRACT = json.loads(
    (Path(__file__).parent / "fixtures/clip_v2_contract.json").read_text(
        encoding="utf-8"
    )
)
RESOURCES = CONTRACT["resources"]
KINDS = [resource["resource_type"] for resource in RESOURCES]


def resource_payload(kind: str) -> dict:
    payload = {
        "id": str(RESOURCE_ID),
        "type": kind,
        "owner": {"rid": str(OWNER_ID), "rtype": "device"},
        "new_firmware_field": {"kept": True},
    }
    if kind == "light":
        payload.update(metadata={"name": "Desk"}, on={"on": True})
    elif kind in {"room", "zone"}:
        payload.update(metadata={"name": "Office", "archetype": "office"})
    elif kind in {"scene", "smart_scene"}:
        payload.update(
            metadata={"name": "Focus"}, group={"rid": str(OWNER_ID), "rtype": "room"}
        )
    elif kind == "entertainment_configuration":
        payload.update(metadata={"name": "TV"})
    return payload


def write_response(kind: str) -> dict:
    return {"data": [{"rid": str(RESOURCE_ID), "rtype": kind}], "errors": []}


@pytest.mark.asyncio
async def test_all_specification_resource_types_have_namespaces(bridge) -> None:
    hue, _, _ = bridge
    assert set(KINDS) <= set(hue.resources.types)


@pytest.mark.asyncio
@pytest.mark.parametrize("kind", KINDS)
async def test_list_and_get_use_specification_paths_and_preserve_response(
    bridge, kind: str
) -> None:
    hue, requests, responses = bridge
    responses.extend([{"data": [resource_payload(kind)]}] * 2)
    namespace = hue.resources[kind]

    listed = await namespace.list()
    fetched = await namespace.get_one(RESOURCE_ID)

    assert fetched == listed.data[0]
    assert isinstance(fetched, m.HueResource)
    assert fetched.type == kind
    assert type(fetched) is not m.HueResource
    assert fetched.model_dump(mode="json")["new_firmware_field"] == {"kept": True}
    assert [(r.method, r.url.path) for r in requests] == [
        ("GET", f"/clip/v2/resource/{kind}"),
        ("GET", f"/clip/v2/resource/{kind}/{RESOURCE_ID}"),
    ]
    assert all(r.headers["hue-application-key"] == "a" * 40 for r in requests)
    assert all(r.url.scheme == "https" for r in requests)


@pytest.mark.asyncio
@pytest.mark.parametrize("resource", RESOURCES, ids=KINDS)
async def test_only_specified_operations_are_exposed_on_typed_namespaces(
    bridge, resource: dict
) -> None:
    hue, _, _ = bridge
    namespace = hue.resources[resource["resource_type"]]
    assert hasattr(namespace, "create") == ("POST" in resource["collection_methods"])
    assert hasattr(namespace, "delete") == ("DELETE" in resource["item_methods"])
    assert hasattr(namespace, "update") == ("PUT" in resource["item_methods"])


PUT_KINDS = [
    resource["resource_type"]
    for resource in RESOURCES
    if "PUT" in resource["item_methods"]
]


@pytest.mark.asyncio
@pytest.mark.parametrize("kind", PUT_KINDS)
async def test_native_updates_use_item_paths_and_keep_bridge_errors(
    bridge, kind: str
) -> None:
    hue, requests, responses = bridge
    responses.append(
        {"data": [], "errors": [{"description": "feature unavailable on this device"}]}
    )
    namespace = hue.resources[kind]
    request_model = {
        "light": m.LightUpdate,
        "grouped_light": m.LightUpdate,
        "room": m.GroupUpdate,
        "zone": m.GroupUpdate,
        "scene": m.SceneUpdate,
        "entertainment_configuration": m.EntertainmentConfigurationUpdate,
    }.get(kind, getattr(namespace, "_update_model", m.HueModel))

    result = await namespace.update(RESOURCE_ID, request_model())

    assert requests[0].method == "PUT"
    assert requests[0].url.path == f"/clip/v2/resource/{kind}/{RESOURCE_ID}"
    assert json.loads(requests[0].content) == {}
    assert result.errors[0].description == "feature unavailable on this device"


@pytest.mark.asyncio
@pytest.mark.parametrize("kind", PUT_KINDS)
async def test_snapshots_cannot_be_sent_as_native_updates(bridge, kind: str) -> None:
    hue, requests, _ = bridge
    snapshot = TypeAdapter(m.AnyHueResource).validate_python(resource_payload(kind))

    with pytest.raises(TypeError, match="update expects"):
        await hue.resources[kind].update(RESOURCE_ID, snapshot)

    assert not requests


@pytest.mark.asyncio
async def test_unspecified_update_schemas_require_an_explicit_request(bridge) -> None:
    hue, requests, responses = bridge
    with pytest.raises(TypeError, match="ResourceUpdate"):
        await hue.bridges.update(RESOURCE_ID, m.HueModel(future_setting=True))
    assert not requests

    responses.append(write_response("bridge"))
    await hue.bridges.update(RESOURCE_ID, m.ResourceUpdate(future_setting=True))

    assert json.loads(requests[0].content) == {"future_setting": True}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "kind",
    [
        resource["resource_type"]
        for resource in RESOURCES
        if "DELETE" in resource["item_methods"]
    ],
)
async def test_deletes_use_specification_paths(bridge, kind: str) -> None:
    hue, requests, responses = bridge
    responses.append(write_response(kind))
    result = await hue.resources[kind].delete(RESOURCE_ID)
    assert requests[0].method == "DELETE"
    assert requests[0].url.path == f"/clip/v2/resource/{kind}/{RESOURCE_ID}"
    assert result.data[0].rid == RESOURCE_ID


@pytest.mark.asyncio
async def test_collection_discovery_parses_mixed_and_future_resources(bridge) -> None:
    hue, requests, responses = bridge
    responses.append(
        {
            "data": [
                resource_payload("light"),
                resource_payload("motion"),
                resource_payload("future_sensor"),
            ]
        }
    )
    result = await hue.resources.list()
    assert requests[0].url.path == "/clip/v2/resource"
    assert isinstance(result.data[0], m.Light)
    assert isinstance(result.data[1], m.Motion)
    assert type(result.data[2]) is m.HueResource
    assert result.model_dump(mode="json")["data"][2]["new_firmware_field"] == {
        "kept": True
    }


@pytest.mark.asyncio
async def test_resource_references_resolve_through_their_namespace(bridge) -> None:
    hue, requests, responses = bridge
    responses.append({"data": [resource_payload("motion")]})
    result = await hue.resources.get(
        m.ResourceReference(rid=RESOURCE_ID, rtype="motion")
    )
    assert isinstance(result, m.Motion)
    assert requests[0].url.path.endswith(f"/motion/{RESOURCE_ID}")


@pytest.mark.asyncio
async def test_raw_requests_preserve_explicit_null_and_future_fields(bridge) -> None:
    hue, requests, responses = bridge
    responses.append(write_response("future_sensor"))
    result = await hue.resources.of("future_sensor").update(
        RESOURCE_ID, {"configuration": None, "future_setting": False}
    )
    assert json.loads(requests[0].content) == {
        "configuration": None,
        "future_setting": False,
    }
    assert result.data[0].rtype == "future_sensor"


@pytest.mark.asyncio
async def test_raw_creation_and_deletion_keep_native_responses(bridge) -> None:
    hue, requests, responses = bridge
    responses.extend([write_response("future_sensor")] * 2)
    raw = hue.resources.of("future_sensor")
    result = await raw.create({"configuration": {"setting": None}})
    await raw.delete(result.data[0].rid)
    assert [(r.method, r.url.path) for r in requests] == [
        ("POST", "/clip/v2/resource/future_sensor"),
        ("DELETE", f"/clip/v2/resource/future_sensor/{RESOURCE_ID}"),
    ]
    assert json.loads(requests[0].content) == {"configuration": {"setting": None}}


@pytest.mark.asyncio
async def test_raw_firmware_resources_can_be_found_by_metadata_name(bridge) -> None:
    hue, _, responses = bridge
    responses.append(
        {"data": [{**resource_payload("future_sensor"), "metadata": {"name": "Desk"}}]}
    )
    assert (
        await hue.resources.of("future_sensor").find_by_name("desk")
    ).id == RESOURCE_ID


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "kind", ["../light", "light/id", "light?x=1", "https://example.org", "", "light#id"]
)
async def test_raw_resource_types_cannot_escape_the_resource_path(
    bridge, kind: str
) -> None:
    hue, requests, _ = bridge
    with pytest.raises(ValueError):
        hue.resources.of(kind)
    assert not requests


@pytest.mark.asyncio
async def test_unnamed_services_are_skipped_during_name_lookup(bridge) -> None:
    hue, _, responses = bridge
    responses.append({"data": [resource_payload("button")]})
    with pytest.raises(ResourceNotFoundError, match="Known names: none"):
        await hue.buttons.find_by_name("Desk")


@pytest.mark.asyncio
async def test_geofence_names_are_found_without_metadata(bridge) -> None:
    hue, _, responses = bridge
    responses.append(
        {"data": [{**resource_payload("geofence_client"), "name": "My phone"}]}
    )
    assert (await hue.geofence_clients.find_by_name(" my PHONE ")).id == RESOURCE_ID


@pytest.mark.asyncio
@pytest.mark.parametrize("kind", ["device", "geofence_client", "future_sensor"])
@pytest.mark.parametrize(
    "query, names", [("DESK", ["Desk", " desk "]), ("Des", ["Desk", "Desi"])]
)
async def test_named_services_and_raw_resources_reject_ambiguous_names(
    bridge, kind: str, query: str, names: list[str]
) -> None:
    hue, _, responses = bridge
    ids = [RESOURCE_ID, OWNER_ID]
    resources = []
    for resource_id, name in zip(ids, names, strict=True):
        payload = {**resource_payload(kind), "id": str(resource_id)}
        payload.update(
            {"name": name}
            if kind == "geofence_client"
            else {"metadata": {"name": name}}
        )
        resources.append(payload)
    responses.append({"data": resources})

    with pytest.raises(AmbiguousResourceError) as caught:
        await hue.resources[kind].find_by_name(query)

    assert all(str(resource_id) in str(caught.value) for resource_id in ids)


@pytest.mark.asyncio
@pytest.mark.parametrize("kind", ["device", "geofence_client", "future_sensor"])
async def test_exact_only_lookup_also_applies_to_services_and_raw_resources(
    bridge, kind: str
) -> None:
    hue, _, responses = bridge
    payload = resource_payload(kind)
    payload.update(
        {"name": "Desk"}
        if kind == "geofence_client"
        else {"metadata": {"name": "Desk"}}
    )
    responses.extend([{"data": [payload]}] * 2)

    with pytest.raises(ResourceNotFoundError):
        await hue.resources[kind].find_by_name("Des", fuzzy=False)
    found = await hue.resources[kind].find_by_name(" DESK ", fuzzy=False)

    assert found.id == RESOURCE_ID


@pytest.mark.asyncio
async def test_empty_reads_raise_resource_not_found(bridge) -> None:
    hue, _, responses = bridge
    responses.append({"data": []})
    with pytest.raises(ResourceNotFoundError):
        await hue.motions.get_one(RESOURCE_ID)


@pytest.mark.asyncio
async def test_http_failures_are_not_hidden(bridge) -> None:
    hue, _, responses = bridge
    responses.append(401)
    with pytest.raises(httpx.HTTPStatusError):
        await hue.motions.list()


def test_scene_creation_requires_its_group_and_actions() -> None:
    with pytest.raises(ValidationError):
        m.SceneCreate(metadata=m.SceneMetadata(name="Focus"))


@pytest.mark.parametrize(
    "model, values",
    [
        (m.EnabledUpdate, {"enabled": False}),
        (m.MotionUpdate, {"sensitivity": {"sensitivity": 0}}),
        (m.DeviceUpdate, {"metadata": {"name": "Renamed"}}),
        (m.GroupUpdate, {"metadata": {"name": "Renamed"}}),
        (m.ServiceGroupUpdate, {"services": []}),
        (m.BehaviorInstanceUpdate, {"configuration": {}, "enabled": False}),
    ],
)
def test_partial_updates_do_not_add_state_or_clear_unrelated_fields(
    model: type[m.HueModel], values: dict
) -> None:
    assert (
        model.model_validate(values).model_dump(mode="json", exclude_none=True)
        == values
    )
