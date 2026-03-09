# Rooms & Zones

`hue.rooms` and `hue.zones` expose [`RoomNamespace`][hueify.grouped_lights.RoomNamespace]
and [`ZoneNamespace`][hueify.grouped_lights.ZoneNamespace] respectively.
Both inherit from [`GroupNamespace`][hueify.grouped_lights.namespace.GroupNamespace] and
share the same control interface.

The difference: **rooms** group physical lights together as configured in the
Hue app; **zones** can span multiple rooms and overlap.

## Listing groups

```python
async with Hueify() as hue:
    print(hue.rooms.names)  # ['Living Room', 'Kitchen', 'Bedroom']
    print(hue.zones.names)  # ['Downstairs', 'Upstairs']
```

## On / Off

```python
await hue.rooms.turn_on("Living Room")
await hue.zones.turn_off("Downstairs")
```

## Brightness

```python
await hue.rooms.set_brightness("Kitchen", 100)
await hue.zones.decrease_brightness("Upstairs", 20)
```

## Scenes

```python
await hue.rooms.activate_scene("Living Room", "Relax")
await hue.rooms.activate_scene("Kitchen", "Energize")
```

## Direct group handle

```python
living_room = hue.rooms.from_name("Living Room")
await living_room.turn_on()
await living_room.activate_scene("Concentrate")
```
