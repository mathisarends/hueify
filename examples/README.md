# Examples

One file per use case. Each script runs standalone once `hueify.onboarding.setup()`
has stored a bridge IP and application key, and each one starts with the resource
names it expects - adjust them to names from your own Hue app.

| File | Use case |
| --- | --- |
| [basic_usage.py](basic_usage.py) | List lights, find one by name, switch it on |
| [lights_control.py](lights_control.py) | Every command a single light understands |
| [rooms_and_zones.py](rooms_and_zones.py) | Control whole rooms and zones, list their lights and scenes |
| [scenes.py](scenes.py) | Find and play scenes, dimmed or as a dynamic palette |
| [colors.py](colors.py) | Hex, color names, RGB tuples, CIE xy and kelvin |
| [transitions.py](transitions.py) | Fade changes over time instead of jumping to them |
| [toggle_lights.py](toggle_lights.py) | Flip whatever state a light is in right now |
| [find_resources.py](find_resources.py) | Names, IDs, envelopes and missing resources |
| [live_state.py](live_state.py) | React to bridge changes over the event stream |
| [server_sent_events.py](server_sent_events.py) | Subscribe to light and scene events |
| [raw_api.py](raw_api.py) | Drop to raw CLIP v2 payloads for effects and gradients |

```bash
uv run examples/basic_usage.py
```
