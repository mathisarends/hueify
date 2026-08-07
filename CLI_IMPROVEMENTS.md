# CLI Improvements

Notes from a hands-on usability pass over `hueify` (built locally via
`uv run --extra cli hueify`, exercised against a real bridge). Goal was to
check discoverability and whether the CLI behaves as expected without prior
knowledge, using only `--help` and trial and error.

## What works well

- `--help` at every level (`hueify`, `hueify light`, `hueify light on`, ...)
  is sufficient to use the whole tool with no external docs. The command
  shape (`resource action target`) is consistent across `light`/`room`/`zone`,
  so behavior is guessable once you've learned one group.
- Unknown-resource errors are excellent: `No light named 'Does Not Exist'.
  Known names: Bettlicht, Deckenlampe, ...` — actionable, no need to re-run
  `list` first.
- Typo recovery works (inherited from Click): `hueify lite list` →
  `No such command 'lite'. Did you mean 'light'?`
- `--plain`, `--json`, and the default table output all work as documented
  and are consistent for `light`/`room`/`zone`/`entertainment`.

## Bug: `scene list` renders raw Python repr

`hueify scene list` prints garbage in the State column:

```
active=<SceneStatusValues... 'inactive'>
last_recall='2026-08-0...
```

Root cause: `hueify/cli/output.py:60`, `_resource_state()` does `str(status)`
on the `SceneStatus` pydantic model instead of reading `status.active`. The
resulting long string overflows the Rich table column width, which then
truncates mid-character — mangling UUIDs and umlauts (`Verträumter`,
`Majestätischer`, `Bernsteinblüte` all show `�`).

`entertainment list` is unaffected because its `status` field is a plain
string/enum, not a nested model.

**Fix:** in `_resource_state`, match `Scene(status=status)` the same way
`Light` is handled — extract `status.active` (e.g. `str(status.active)` or
`status.active.value if status.active else ""`) instead of stringifying the
whole model.

## Inconsistency: validation error messages

- `hueify light color <target> notahex` → clean, custom message:
  `Invalid hex color 'notahex': expected '#rgb' or '#rrggbb'`
- `hueify light brightness <target> 150` → raw Pydantic `ValidationError`
  leaks through, including a link to the pydantic docs:
  ```
  1 validation error for DimmingState
  brightness
    Input should be less than or equal to 100 [type=less_than_equal, ...]
      For further information visit https://errors.pydantic.dev/2.12/v/less_than_equal
  ```

Both hit exit code `2` (matches the documented contract), but only one has a
curated message. Worth catching the pydantic `ValidationError` for
brightness/temperature/etc. and re-raising as the same kind of plain
`ValueError` the hex-color path already uses, so all input validation reads
the same way.

## Minor friction: global output flags must precede the subcommand

`--json` / `--plain` / `--no-color` only work before the resource group:

```
hueify --json light list      # works
hueify light list --json      # "No such option: --json"
```

This is standard Typer/Click behavior for command groups, not a bug, but
it's the one place where muscle memory from flatter CLIs trips up. Not
proposing a fix — just noting it as the single discoverability snag in an
otherwise predictable CLI.

## Side note: stale global install

The globally `pip`-installed `hueify` on this machine was v0.5.1, well
behind this branch (0.8.1) — old plural group names (`lights`/`rooms`/`zones`),
no `scene`/`entertainment`/`--version`/`--json`/`--plain`. Not a code issue,
just a heads-up: if PyPI is still serving 0.5.1, anyone following the current
README against a `pip install hueify[cli]` will land on the old CLI shape
until this branch ships.
