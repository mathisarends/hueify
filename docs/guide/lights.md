# Lights

`hue.lights` exposes the [`LightNamespace`][hueify.light.LightNamespace] and
lets you control individual bulbs by name.

## Listing lights

```python
async with Hueify() as hue:
    print(hue.lights.names)  # ['Desk', 'Floor Lamp', 'Ceiling']
```

## On / Off

```python
await hue.lights.turn_on("Desk")
await hue.lights.turn_off("Desk")
```

## Brightness

```python
await hue.lights.set_brightness("Desk", 80)        # 80 %
await hue.lights.increase_brightness("Desk", 10)   # +10 %
await hue.lights.decrease_brightness("Desk", 10)   # -10 %

current = hue.lights.get_brightness("Desk")
```

## Colour temperature

```python
# 0 = warmest white, 100 = coolest white
await hue.lights.set_color_temperature("Desk", 30)
```

## Direct light handle

For multiple operations on the same light, grab a
[`Light`][hueify.Light] handle to avoid repeated cache lookups:

```python
desk = hue.lights.from_name("Desk")
await desk.turn_on()
await desk.set_brightness(60)
```
