# CLIP v2 coverage and migration

The endpoint inventory is pinned to [OpenHue API revision
1ffc817](https://github.com/openhue/openhue-api/tree/1ffc817857abf456d5ff2ae50400ef768dbce28e),
retrieved on 2026-10-04. The inventory is reproduced as interface facts in
`tests/fixtures/clip_v2_contract.json`; no download is needed to run tests.
OpenHue publishes its specification under Apache-2.0. Hueify's independently
implemented Python client remains MIT licensed.

Every one of the 41 resource types with endpoints in that revision has a
namespace, concrete response model, and partial event model. GET supports both
collection and item reads. POST targets the collection; PUT and DELETE target
an item. The resource root, SSE event stream, registration and existing
entertainment transport are also available.

This covers the pinned public specification. It is not a certification of
completeness against the authenticated Philips Hue developer reference or a
claim that every feature is available on every bridge. The public spec omits
some writable fields and advanced creation/deletion workflows.

## Namespace inventory

Each namespace exposes `list()`, `get(id)` and `get_one(id)`. `find_by_name()`
uses metadata names or a native name field and skips unnamed services. It
raises ResourceNotFoundError if no named resource matches.

| Resource | Namespace | Response model | Native operations | Update model |
| --- | --- | --- | --- | --- |
| `behavior_instance` | `hue.behavior_instances` | `BehaviorInstance` | GET / PUT | `BehaviorInstanceUpdate` |
| `behavior_script` | `hue.behavior_scripts` | `BehaviorScript` | GET / PUT | `HueModel` |
| `bell_button` | `hue.bell_buttons` | `BellButton` | GET / PUT | `HueModel` |
| `bridge` | `hue.bridges` | `Bridge` | GET / PUT | `HueModel` |
| `bridge_home` | `hue.bridge_homes` | `BridgeHome` | GET | N/A |
| `button` | `hue.buttons` | `Button` | GET / PUT | `ButtonUpdate` |
| `camera_motion` | `hue.camera_motions` | `CameraMotion` | GET / PUT | `EnabledUpdate` |
| `contact` | `hue.contacts` | `Contact` | GET / PUT | `EnabledUpdate` |
| `convenience_area_motion` | `hue.convenience_area_motions` | `ConvenienceAreaMotion` | GET / PUT | `EnabledUpdate` |
| `device` | `hue.devices` | `Device` | GET / PUT / DELETE | `DeviceUpdate` |
| `device_power` | `hue.device_power` | `DevicePower` | GET | N/A |
| `device_software_update` | `hue.device_software_updates` | `DeviceSoftwareUpdate` | GET / PUT | `DeviceSoftwareUpdateUpdate` |
| `entertainment` | `hue.entertainment_services` | `Entertainment` | GET / PUT | `HueModel` |
| `entertainment_configuration` | `hue.entertainment` | `EntertainmentConfiguration` | GET / PUT | `EntertainmentConfigurationUpdate` |
| `geofence_client` | `hue.geofence_clients` | `GeofenceClient` | GET / PUT | `GeofenceClientUpdate` |
| `geolocation` | `hue.geolocations` | `Geolocation` | GET / PUT | `HueModel` |
| `grouped_light` | `hue.grouped_lights` | `GroupedLight` | GET / PUT | `LightUpdate` |
| `grouped_light_level` | `hue.grouped_light_levels` | `GroupedLightLevel` | GET / PUT | `HueModel` |
| `grouped_motion` | `hue.grouped_motions` | `GroupedMotion` | GET / PUT | `HueModel` |
| `homekit` | `hue.homekit` | `Homekit` | GET / PUT | `HomekitUpdate` |
| `light` | `hue.lights` | `Light` | GET / PUT | `LightUpdate` |
| `light_level` | `hue.light_levels` | `LightLevel` | GET / PUT | `EnabledUpdate` |
| `matter` | `hue.matter` | `Matter` | GET / PUT | `MatterUpdate` |
| `matter_fabric` | `hue.matter_fabrics` | `MatterFabric` | GET / PUT | `HueModel` |
| `motion` | `hue.motions` | `Motion` | GET / PUT | `MotionUpdate` |
| `motion_area_candidate` | `hue.motion_area_candidates` | `MotionAreaCandidate` | GET / PUT | `HueModel` |
| `motion_area_configuration` | `hue.motion_area_configurations` | `MotionAreaConfiguration` | GET / PUT | `EnabledUpdate` |
| `relative_rotary` | `hue.relative_rotaries` | `RelativeRotary` | GET / PUT | `HueModel` |
| `room` | `hue.rooms` | `Room` | GET / PUT / DELETE / POST | `GroupUpdate` |
| `scene` | `hue.scenes` | `Scene` | GET / PUT / DELETE / POST | `SceneUpdate` |
| `security_area_motion` | `hue.security_area_motions` | `SecurityAreaMotion` | GET / PUT | `EnabledUpdate` |
| `service_group` | `hue.service_groups` | `ServiceGroup` | GET / PUT | `ServiceGroupUpdate` |
| `smart_scene` | `hue.smart_scenes` | `SmartScene` | GET / PUT / DELETE / POST | `SmartSceneUpdate` |
| `speaker` | `hue.speakers` | `Speaker` | GET / PUT | `HueModel` |
| `tamper` | `hue.tampers` | `Tamper` | GET / PUT | `HueModel` |
| `temperature` | `hue.temperatures` | `Temperature` | GET / PUT | `EnabledUpdate` |
| `wifi_connectivity` | `hue.wifi_connectivity` | `WifiConnectivity` | GET / PUT | `HueModel` |
| `zgp_connectivity` | `hue.zgp_connectivity` | `ZgpConnectivity` | GET / PUT | `HueModel` |
| `zigbee_connectivity` | `hue.zigbee_connectivity` | `ZigbeeConnectivity` | GET / PUT | `ZigbeeConnectivityUpdate` |
| `zigbee_device_discovery` | `hue.zigbee_device_discovery` | `ZigbeeDeviceDiscovery` | GET / PUT | `ZigbeeDeviceDiscoveryUpdate` |
| `zone` | `hue.zones` | `Zone` | GET / PUT / DELETE / POST | `GroupUpdate` |

A `HueModel` update in the table means the pinned PUT schema specifies no
mutable properties beyond the resource type. Hueify permits explicit extra
fields for firmware additions without asserting their meaning or support.
Read-only services have no typed create, update or delete method.

`hue.entertainment` keeps the existing entertainment-area and streaming API;
`hue.entertainment_services` addresses the individual `entertainment` services.
`hue.grouped_lights` addresses a grouped light ID directly. Room and zone
commands continue to resolve their grouped light service first.

## Native reads, references and raw requests

```python
from hueify import Hueify
from hueify.models import DeviceUpdate, MetadataUpdate

async with Hueify() as hue:
    all_resources = await hue.resources.list()
    light = await hue.lights.find_by_name("Desk")
    device = await hue.resources.get(light.owner)
    await hue.devices.update(
        device.id, DeviceUpdate(metadata=MetadataUpdate(name="Desk lamp"))
    )
```

`hue.resources[ResourceType.MOTION]` and `hue.resources["motion"]` return the
built-in motion namespace. `hue.resources.types` lists client-supported types;
`hue.resources.list()` reports the actual resources exposed by the bridge.
Unknown resource types and reference types remain usable after firmware
upgrades. All unknown fields survive a JSON round trip.

`hue.resources.of(type)` returns a raw namespace with read/create/update/delete
operations and accepts dictionaries or Pydantic models. The bridge decides
whether those operations and payloads are supported. Dictionary payloads
preserve explicit JSON nulls:

```python
await hue.resources.of("light").update(light.id, {"future_setting": None})
```

Typed update models omit optional None fields. Use the raw dictionary path
when an operation explicitly requires a JSON null. Errors in successful HTTP
responses remain in `HueApiResponse.errors`; HTTP errors raise
`httpx.HTTPStatusError`. `get_one()` raises ResourceNotFoundError for empty data.

## Task-oriented commands

- Devices: `rename`, `identify`, `set_usertest`, `delete`.
- Motion: `enable`, `disable`, `set_sensitivity`. Other switchable sensor
  namespaces and behavior instances expose `enable` and `disable`.
- Device software updates: `install`; Zigbee discovery: `search`.
- Geofence clients: `set_at_home`; HomeKit and Matter: `reset`.
- Smart scenes: `create`, `update`, `delete`, `activate`, `deactivate`.
- Lights: `set_effect` and `stop_effect` use `effects_v2`; `set_gradient`,
  `set_timed_effect`, `stop_timed_effect` and `set_powerup_preset` cover their
  feature payloads. Power-up presets change configuration without turning on
  the light. Custom power-up settings use `LightUpdate(powerup=...)` or raw JSON.
- Lights, grouped lights, rooms and zones: `signal`, `warmer`, `cooler`,
  `stop_color_temperature`, `stop_dimming` in addition to the original commands.
  Warmer increases mirek, cooler decreases it. Those relative commands and
  stop commands do not change on/off state.

Durations in convenience methods accept seconds or timedelta; native request
models use milliseconds. A gradient write needs 2 to 5 ordered points. Signal
colors serialize under singular `color`, as ColorState objects containing xy.
The bridge validates reported capabilities, feature availability and
resource-dependent limits, including sensitivity_max and gradient capability.

## Creating a smart scene

Smart-scene slots reference existing scenes. Replace the UUIDs below with a
room or zone and scenes in that group.

```python
from hueify.models import (
    MetadataUpdate, ResourceReference, SmartSceneCreate, SmartSceneDay,
    SmartSceneStartTime, SmartSceneTime, SmartSceneTimeslot,
)

request = SmartSceneCreate(
    metadata=MetadataUpdate(name="Working day"),
    group=ResourceReference(rid=room_id, rtype="room"),
    transition_duration=60000,
    week_timeslots=[SmartSceneDay(
        recurrence=["monday", "tuesday", "wednesday", "thursday", "friday"],
        timeslots=[
            SmartSceneTimeslot(
                start_time=SmartSceneStartTime(
                    kind="time", time=SmartSceneTime(hour=8, minute=0)
                ),
                target=ResourceReference(rid=focus_scene_id, rtype="scene"),
            ),
            SmartSceneTimeslot(
                start_time=SmartSceneStartTime(kind="sunset"),
                target=ResourceReference(rid=relax_scene_id, rtype="scene"),
            ),
        ],
    )],
)
result = await hue.smart_scenes.create(request)
if result.data:
    await hue.smart_scenes.activate(result.data[0].rid)
```

Clock hours, minutes and seconds are validated. A clock start requires a time;
a sunset start omits it. Sensor accessors prefer timestamped report values
over deprecated scalar fields and return None for invalid legacy readings.
Light levels convert the bridge's logarithmic units to lux.

## Partial events

Every modeled resource has its own event class, such as MotionEvent,
ButtonEvent, DeviceEvent, SmartSceneEvent and GroupedLightEvent. Event fields
may be absent. Lists such as device services stay None when absent, distinct
from an explicit empty list. Unknown resource types use HueEvent and retain
all their fields. Subscribe using `hue.on(ResourceType.MOTION)` or a type string.

## Breaking changes

- `scenes.create` now requires SceneCreate, including metadata, group and
  actions. `rooms.create` and `zones.create` require GroupCreate; empty children
  are supported. Update models remain partial and are rejected by create.
- LightUpdate uses GradientUpdate, EffectsV2Update and SignalingUpdate for
  those writable features. Snapshot models still describe the read state.
- GroupMetadataUpdate and SceneMetadataUpdate support metadata-only partial
  changes without requiring unrelated fields.
- ScenePalette.dimming contains DimmingState objects directly, and
  ScenePalette.effects contains EffectAction objects. Color and color-temperature
  palette entries retain their optional dimming.
- Sensor and other service events now arrive as their typed event class.
  ResourceType retains unknown firmware values while preserving enum identity
  for the built-in values.

## Reference and hardware checks still required

The [official developer portal](https://developers.meethue.com/develop/hue-api-v2/api-reference/)
is the authority for current firmware behavior. Its authenticated contents
were unavailable for independent schema verification in this implementation.

- The public [Hue announcements](https://developers.meethue.com/) document
  `switch_input_configuration` replacing device_mode. The corresponding
  `hue.switch_input_configurations` namespace and event retain switch_mode,
  including an object or string form; exact modes, shape and capabilities
  require the current authenticated reference.
- OpenHue includes reads and limited updates for MotionAware resources, but
  omits full area creation/configuration and Bridge Pro migration workflows.
  These have no invented typed helpers. Use a raw namespace with a payload
  obtained from the official documentation.
- Custom power-up structures, richer entertainment-area management,
  behavior-instance creation/deletion, geolocation writes and integration
  commissioning operations have incomplete public schemas. Raw namespaces
  keep those bridge endpoints reachable without claiming schema validation.
- Actual device effects, sensor tuning, Matter/HomeKit resets, software
  installs, discovery, MotionAware and DTLS streaming need compatible hardware.
  Automated tests use mocked HTTPS responses and transports; they make no
  changes to a physical bridge.

## Verification

```bash
uv sync --extra entertainment
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

The suite checks every pinned resource's collection/item HTTP path and
operation availability, concrete read types, native error envelopes, exact
command payloads, creation requirements, invalid-value rejection before
network access, sparse events, unknown firmware fields and raw null handling.
Existing CLI, SSE reconnect and entertainment tests remain part of the suite.
Runnable read/event examples are in examples/resource_inventory.py and
examples/sensors_and_devices.py.
