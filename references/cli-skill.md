---
name: hueify-cli
description: Control Philips Hue lights, rooms, and zones from the terminal with the `hueify` CLI — turn lights on/off, set or nudge brightness, set colour temperature, and list/activate scenes. Use whenever the user asks to change or inspect the state of their Hue lighting ("turn off the kitchen", "dim the living room to 30%", "which scene is active", "warmer light in the office").
---

# Hueify CLI

`hueify` is a Typer CLI over the Philips Hue Bridge API. Three command groups mirror
the Hue resource model:

| Group | Controls | Has scenes |
|---|---|---|
| `hueify lights` | a single bulb | no |
| `hueify rooms` | all bulbs in a room | yes |
| `hueify zones` | all bulbs in a zone | yes |

Rooms and zones both group bulbs; a bulb belongs to exactly one room but can be in
any number of zones. When the user names a place ("kitchen", "office"), it is almost
always a room — start with `hueify rooms list`.

## Before doing anything: discover the real names

Every command addresses resources by name, and the names are whatever the user chose
in the Hue app. Never guess them. List first, then act:

```bash
hueify lights list
hueify rooms list
hueify zones list
```

Matching is case-insensitive but otherwise exact. Quote names containing spaces:

```bash
hueify rooms on "Living Room"
```

An unknown name exits 1 with fuzzy suggestions, e.g.
`Not found: Room 'kitcen' not found. Did you mean: 'Kitchen', 'Kids Room'?` —
re-run with the suggested spelling rather than listing again.

## Commands

Every command below exists identically for `lights`, `rooms`, and `zones`.
`<name>` is a light/room/zone name.

```bash
hueify <group> list                          # names of all resources in the group
hueify <group> info <name>                   # on/off, brightness, temperature (+ scenes for rooms/zones)
hueify <group> on <name>
hueify <group> off <name>
hueify <group> brightness <name> <0-100>     # absolute
hueify <group> brightness-up <name> <0-100>  # relative, add
hueify <group> brightness-down <name> <0-100># relative, subtract
hueify <group> brightness-get <name>
hueify <group> temperature <name> <0-100>
```

Scenes exist only for `rooms` and `zones`:

```bash
hueify rooms scenes <name>                   # all scenes, active one marked
hueify rooms active-scene <name>
hueify rooms activate-scene <name> <scene>   # scene name, also case-insensitive
```

### Brightness

Percentages in `[0, 100]`. Out-of-range values are **clamped, not rejected** — the
command still succeeds and the output is suffixed `(clamped)`. So
`brightness-up "Kitchen" 50` on a light already at 80% lands at 100% and reports
success. If the user asked for a precise level, verify with `brightness-get` rather
than assuming the delta applied in full.

Prefer `brightness-up`/`brightness-down` for "a bit brighter/dimmer" and
`brightness` for "set it to 40%".

### Colour temperature

`temperature <name> <0-100>` sets the white tone as a percentage of whatever range the
bulb supports; it clamps the same way brightness does. Bulbs without colour-temperature
support omit the `Temperature:` row in `info`. There is no RGB/colour command.

## Working with the output

Output is Rich-formatted text for humans — there is no `--json` flag and no
machine-readable mode. Parse it loosely or, better, read the value you need from the
dedicated command (`brightness-get`, `active-scene`) instead of scraping `info`.

- mutations print `✓ <message>`, or `✓ <message> (clamped)`
- failures print `✗ <message>` or `Error: …` to **stderr** and exit 1
- exit codes: `0` success, `1` any error (unknown name, bridge unreachable),
  `130` interrupted

Each invocation opens a fresh connection to the bridge and re-fetches state, so a
batch of commands is several round trips. Chain them anyway — there is no batch
mode — but keep batches small and avoid tight loops over many lights; the bridge
rate-limits.
