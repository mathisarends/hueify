# Hueify

Hueify is a Python library for convenient control of Philips Hue lighting systems. The library provides an intuitive and asynchronous API for managing Hue groups, scenes, and lights.

## Features

- **Asynchronous API**: All operations use Python's asyncio for efficient, non-blocking I/O
- **Group Control**: Easy management of light groups (rooms and zones)
- **Scene Support**: Activate and manage scenes
- **State Management**: Save and restore light states
- **Brightness Control**: Convenient methods for percentage-based brightness adjustment

## Installation

```bash
pip install hueify
```

## Configuration

Hueify requires two environment variables:

- `HUE_BRIDGE_IP`: The IP address of your Philips Hue Bridge
- `HUE_USER_ID`: The user ID for authentication with the Bridge

These can be stored in a `.env` file in your project directory or as system environment variables.

### .env Example:

```
HUE_BRIDGE_IP=192.168.1.100
HUE_USER_ID=abcdefghijklmnopqrstuvwxyz
```

### How to Get Your Hue User ID (HUE_USER_ID)

If you're using your Hue Bridge with this library for the first time, you need to generate a user ID for authentication:

1. **Press the physical button** on the top of your Hue Bridge. This allows registration of a new user for a short time (about 30 seconds).
2. **Send a POST request to the Bridge API** (replace `<bridge-ip>` with your actual IP):

```bash
curl -X POST -H "Content-Type: application/json" \
-d '{"devicetype":"hueify#your_device"}' \
http://<bridge-ip>/api
```

3. **Get the username from the response**, which looks like this:

```json
[{ "success": { "username": "your-generated-username" } }]
```

4. **Save this username** in your `.env` file as `HUE_USER_ID`.

⚠️ Make sure to press the bridge button **right before** running the request. If not, you will get an error like `"link button not pressed"`.

## Usage

### Example: Group Control

```python
import asyncio
from hueify.bridge import HueBridge
from hueify.controllers.group_controller import GroupsManager

async def main():
    # Connect to the Bridge
    bridge = HueBridge()

    # Initialize the groups manager
    groups_manager = GroupsManager(bridge)

    # Get a controller for a group (by name or ID)
    living_room = await groups_manager.get_controller("Living Room")

    # Display information
    print(f"Group: {living_room.name} (ID: {living_room.group_id})")

    # Turn on lights
    await living_room.turn_on()

    # Set brightness to 50%
    await living_room.set_brightness_percentage(50)

    # Activate a scene
    await living_room.activate_scene("Relax")

    # Save current state
    state_id = await living_room.save_state("my_state")

    # Increase brightness
    await living_room.increase_brightness_percentage(20)

    # Restore state
    await living_room.restore_state(state_id)

    # Turn off lights
    await living_room.turn_off()

if __name__ == "__main__":
    asyncio.run(main())
```

### Listing All Available Groups

```python
import asyncio
from hueify.bridge import HueBridge
from hueify.controllers.group_controller import GroupsManager

async def list_groups():
    bridge = HueBridge()
    groups_manager = GroupsManager(bridge)

    # Output formatted list of all groups
    groups_list = await groups_manager.get_available_groups_formatted()
    print(groups_list)

if __name__ == "__main__":
    asyncio.run(list_groups())
```

## Common Use Cases

### Smart Home Automation

```python
import asyncio
from hueify.bridge import HueBridge
from hueify.controllers.group_controller import GroupsManager

async def morning_routine():
    """Gradually increase lights in the bedroom and kitchen for a gentle wake-up."""
    bridge = HueBridge()
    groups = GroupsManager(bridge)

    # Turn on bedroom lights at 10%
    bedroom = await groups.get_controller("Bedroom")
    await bedroom.set_brightness_percentage(10, transition_time=30)  # 3 second fade-in

    # Wait 5 minutes
    await asyncio.sleep(300)

    # Increase to 40%
    await bedroom.set_brightness_percentage(40, transition_time=100)  # 10 second transition

    # Turn on kitchen lights
    kitchen = await groups.get_controller("Kitchen")
    await kitchen.set_brightness_percentage(70)

if __name__ == "__main__":
    asyncio.run(morning_routine())
```

### Movie Night Scene

```python
import asyncio
from hueify.bridge import HueBridge
from hueify.controllers.group_controller import GroupsManager

async def movie_night():
    """Set up the perfect lighting for movie night."""
    bridge = HueBridge()
    groups = GroupsManager(bridge)

    # Get controllers for relevant rooms
    living_room = await groups.get_controller("Living Room")
    kitchen = await groups.get_controller("Kitchen")
    hallway = await groups.get_controller("Hallway")

    # Save current states to restore later
    lr_state = await living_room.save_state("pre_movie")

    # Set living room to movie scene or dim the lights
    try:
        await living_room.activate_scene("Movie")
    except:
        # If scene doesn't exist, dim to 15%
        await living_room.set_brightness_percentage(15)

    # Turn kitchen lights to low
    await kitchen.set_brightness_percentage(30)

    # Dim hallway lights
    await hallway.set_brightness_percentage(20)

    print("Movie mode activated! Enjoy your film.")

    # To restore after movie:
    # await living_room.restore_state("pre_movie")

if __name__ == "__main__":
    asyncio.run(movie_night())
```

## Development

### Requirements

- Python 3.9 or higher
- A Philips Hue Bridge
- A registered user ID on the Bridge

### Development Setup

1. Clone the repository
2. Install dependencies
   ```bash
   pip install -e .
   pip install -r requirements.txt
   ```
3. Create a `.env` file with your Bridge details

### Running Tests

```bash
pytest tests/
```

## License

[MIT](LICENSE)

## Contributing

Contributions are welcome! Please open an issue first to discuss changes before submitting pull requests.
