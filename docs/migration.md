# Migration guide

## From `v0.9.0` to Unreleased

This guide compares the repository tag `v0.9.0` with the current development
version. **Unreleased is not a package version.** The tag itself declares
`0.8.1` in `pyproject.toml`; check the actual installed version and source when
planning an upgrade. See [CHANGELOG.md](../CHANGELOG.md) for the change list.

### Breaking: create and update payloads

`rooms.create` and `zones.create` now require `GroupCreate`, while
`scenes.create` requires `SceneCreate`. Continue to use `GroupUpdate` and
`SceneUpdate` for updates. A scene create requires metadata, a room or zone
reference, and actions targeting lights; group creation requires metadata and
accepts an empty children list.

```python
from hueify.models import (
    GroupCreate, GroupMetadata, GroupMetadataUpdate, GroupUpdate,
    LightUpdate, OnState, ResourceReference, SceneActionTarget,
    SceneCreate, SceneMetadata,
)

# Previously: hue.rooms.create(GroupUpdate(metadata=..., children=...))
await hue.rooms.create(GroupCreate(
    metadata=GroupMetadata(name="Office", archetype="office"),
    children=[],
))
await hue.rooms.update(room_id, GroupUpdate(
    metadata=GroupMetadataUpdate(name="Office upstairs"),
))

# Previously: hue.scenes.create(SceneUpdate(...))
await hue.scenes.create(SceneCreate(
    metadata=SceneMetadata(name="Focus"),
    group=ResourceReference(rid=room_id, rtype="room"),
    actions=[SceneActionTarget(
        target=ResourceReference(rid=light_id, rtype="light"),
        action=LightUpdate(on=OnState(on=True)),
    )],
))
```

Typed writes now check the expected request model; `apply` and scene `recall`
also reject the wrong model type. Typed requests reject unknown fields,
including nested fields, and some values have stricter validation. Replace
snapshot/event objects and arbitrary fields with the appropriate update model.
For example, use `LightUpdate(dimming=DimmingState(brightness=50))` rather
than `LightUpdate(brightness=50)`. For fields outside the typed schema, use an
explicit raw namespace, e.g.
`await hue.resources.of("light").update(light_id, {"future_setting": None})`.
`ResourceUpdate` remains open for explicitly unspecified update schemas.
Raw requests depend on bridge support. See the
[coverage guide](clip-v2-coverage.md#namespace-inventory) for request models.

For `LightUpdate.gradient` and `LightUpdate.signaling`, replace
`GradientState` and `SignalingState` with `GradientUpdate` and
`SignalingUpdate`. Signaling uses singular `color`, containing `ColorState`
objects. New `effects_v2` writes use `EffectsV2Update`. Alternatively, use
`hue.lights.set_gradient(...)` and `hue.lights.signal(...)`.

`ScenePalette.dimming` now contains `DimmingState` directly instead of
`DimmingPaletteEntry`; `effects` contains `EffectAction` instead of
`EffectsPaletteEntry`, and `effects_v2` uses `EffectsV2PaletteEntry`.
Update both construction and code reading these lists. Palette values must also
satisfy the new schema limits.

### Breaking: entertainment brightness and stream errors

`EntertainmentStream.set`, `set_all`, `Frame.set`, `set_all`, and
`hueify.entertainment.protocol.to_stream_rgb` now accept the brightness as a
keyword-only fraction between 0 and 1:

```python
# Before: stream.set_all("#ff8800", 0.4)
# Before: frame.set(0, "blue", brightness=0.4)
stream.set_all("#ff8800", brightness_fraction=0.4)
frame.set(0, "blue", brightness_fraction=0.4)
```

REST command `brightness` still uses percent (0–100). Stream startup now fails
when the bridge rejects activation or the DTLS handshake is not confirmed;
handle the exception instead of assuming the stream opened. `wait_closed()`
re-raises a stored sender error even after `close()`; catch it where shutdown
is awaited. A successful subsequent `open()` clears the previous error and
resets statistics.

### Breaking: lookups and bridge errors

`get_one()` and `find_by_name()` now raise `BridgeError` when the bridge
returns API errors, including partial-success responses. Previously these
unwrapped reads could ignore errors. Catch `BridgeError` and inspect `.errors`,
or use `get()` / `list()` to inspect the envelope explicitly. Empty successful
lookups still raise `ResourceNotFoundError`.

Duplicate exact names and tied best fuzzy matches now raise
`AmbiguousResourceError` instead of selecting a resource. Persist and use IDs;
for scenes, use `await hue.scenes.find_by_name("Focus", group_id=room_id)` to
scope the lookup. Use `fuzzy=False` if only an exact name is acceptable; it
does not resolve duplicate exact names. The CLI has `--room`, `--zone` and
`--no-fuzzy` equivalents.

### Breaking: event handling and CLI failures

Event classes are partial read models, no longer subclasses of writable update
models. Construct an explicit request from the fields you intend to write
instead of passing an event to an update method. Sensor and service events now
have dedicated types. An unknown resource type can arrive as `HueEvent` with
its type preserved; avoid exhaustive assumptions about known types.

Events are processed in arrival order through a bounded queue; handlers for one
event finish before the next begins. On reconnect, queued handlers finish before
connected callbacks run. Do not make a queued handler wait for a connected
callback, or the two can deadlock. Stopping cancels active handlers and discards
pending events; callbacks requesting stop should return promptly. See
[Event stream](../README.md#event-stream) for lifecycle and resync details.

CLI commands now exit unsuccessfully when the bridge returns an error envelope.
Update scripts that relied on a successful exit despite a bridge error to handle
the failure. The [CLI documentation](../README.md#cli) lists exit codes.

### Upgrade checklist for agents

1. Search for `GroupUpdate` / `SceneUpdate` passed to `create`, stream or
   frame `brightness`, and positional brightness arguments; migrate them above.
2. Audit typed writes, palette construction and event-to-update conversions.
3. Handle `BridgeError`, ambiguous names, CLI failures and stream failures;
   review event ordering and reconnect callbacks.
4. Run the consuming project's tests, including bridge mocks and any available
   hardware integration checks.
