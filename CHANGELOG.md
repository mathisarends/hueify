# Changelog

All notable changes are recorded here. Changes under **Unreleased** are
compared with the repository tag `v0.9.0`; they are not a published release.
For each future change, update this section in the same commit. Mark incompatible
changes **Breaking** and link to actionable before/after migration instructions
in [the migration guide](docs/migration.md). At release time, move the entries
under a version and date and start a new Unreleased section.

## Unreleased

### Breaking

The [migration guide](docs/migration.md#from-v090-to-unreleased) describes the
required changes and examples for agents and maintainers.

- Scene, room and zone creation require dedicated create models; typed writes
  validate request types and fields. Gradient and signaling write payloads use
  dedicated update models, and scene palette shapes have changed.
- Entertainment stream and frame brightness is now the keyword-only
  `brightness_fraction`; the same applies to `to_stream_rgb`.
- Unwrapped reads raise `BridgeError` for bridge errors, and ambiguous name
  lookups raise `AmbiguousResourceError` instead of choosing a candidate.
- Events use partial event models rather than writable update models; event
  delivery, reconnect ordering and shutdown have changed.
- Entertainment stream startup requires a successful bridge response and DTLS
  handshake; `wait_closed()` retains and raises a sender error after closing.
- CLI commands return failure exit codes when the bridge reports errors.

### Added

- Typed CLIP v2 resource namespaces, request and event models, mixed resource
  inventory, reference lookup and an explicit raw-resource escape hatch.
- Direct grouped-light commands; light effects, gradients, timed effects,
  power-up and signaling helpers; smart-scene and sensor commands.
- Scene lookup scoped to a room or zone, exact-only name lookup, configurable
  REST timeout, TLS verification and transport, and bounded SSE event queues.

### Fixed

- Preserve unknown resource types and event metadata, isolate malformed events,
  validate merged credentials, and improve SSE lifecycle handling.
- Confirm, retry, order and deduplicate DTLS handshake messages; reject failed
  entertainment-area starts and preserve stream errors and statistics.
- Reduce response parsing allocations and namespace overhead.

The `v0.9.0` tag currently contains package version `0.8.1` in
`pyproject.toml`. Resolve the release version explicitly before publishing;
the tag alone does not determine the installed package version.
