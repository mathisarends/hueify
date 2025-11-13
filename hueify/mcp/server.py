from fastmcp import FastMCP

from hueify.groups import RoomController, RoomLookup, ZoneController, ZoneLookup
from hueify.lights import LightController, LightLookup
from hueify.scenes import SceneLookup, ShortSceneInfo
from hueify.shared.controller import ActionResult

mcp = FastMCP("Hueify MCP Server")

# ===== Lights =====


@mcp.tool(
    description=(
        "Discover all available light names. "
        "Use this to see what lights are available before controlling them."
    )
)
async def discover_light_names() -> str:
    lookup = LightLookup()
    light_names = await lookup.get_light_names()
    return "\n".join(light_names)


@mcp.tool(
    description=(
        "Turn on a specified light by name. "
        "Try the light name directly - if not found, you'll get an error with available names to choose from."
    )
)
async def turn_on_light(light_name: str) -> ActionResult:
    controller = await LightController.from_name(light_name)
    return await controller.turn_on()


@mcp.tool(
    description=(
        "Turn off a specified light by name. "
        "Try the light name directly - if not found, you'll get an error with available names to choose from."
    )
)
async def turn_off_light(light_name: str) -> ActionResult:
    controller = await LightController.from_name(light_name)
    return await controller.turn_off()


@mcp.tool(
    description=(
        "Set the brightness of a specified light by name. "
        "Try the light name directly - if not found, you'll get an error with available names to choose from."
    )
)
async def set_light_brightness(
    light_name: str, percentage: float | int
) -> ActionResult:
    controller = await LightController.from_name(light_name)
    return await controller.set_brightness_percentage(percentage)


@mcp.tool(
    description=(
        "Increase the brightness of a specified light by name. "
        "Try the light name directly - if not found, you'll get an error with available names to choose from."
    )
)
async def increase_light_brightness(
    light_name: str, percentage: float | int
) -> ActionResult:
    controller = await LightController.from_name(light_name)
    return await controller.increase_brightness_percentage(percentage)


@mcp.tool(
    description=(
        "Decrease the brightness of a specified light by name. "
        "Try the light name directly - if not found, you'll get an error with available names to choose from."
    )
)
async def decrease_light_brightness(
    light_name: str, percentage: float | int
) -> ActionResult:
    controller = await LightController.from_name(light_name)
    return await controller.decrease_brightness_percentage(percentage)


@mcp.tool(
    description=(
        "Set the color temperature of a specified light by name. "
        "Try the light name directly - if not found, you'll get an error with available names to choose from."
    )
)
async def set_light_color_temperature(
    light_name: str, percentage: float | int
) -> ActionResult:
    controller = await LightController.from_name(light_name)
    return await controller.set_color_temperature_percentage(percentage)


# ===== Rooms =====


@mcp.tool(
    description=(
        "Discover all available rooms. "
        "Rooms are physical spaces that group lights together (e.g., 'Living Room', 'Kitchen'). "
        "Use rooms when the user refers to controlling lights in a specific physical location."
    )
)
async def discover_rooms() -> list[str]:
    room_lookup = RoomLookup()
    rooms = await room_lookup.get_all_entities()
    return [room.name for room in rooms]


@mcp.tool(
    description=(
        "Turn on all lights in a room. "
        "Try the room name directly - if not found, you'll get an error with available names to choose from. "
        "Use this when the user wants to control lights in a physical space/room. "
        "This is preferred over individual light control for general commands like 'turn on my lights'."
    )
)
async def turn_on_room(room_name: str) -> ActionResult:
    controller = await RoomController.from_name(room_name)
    return await controller.turn_on()


@mcp.tool(
    description=(
        "Turn off all lights in a room. "
        "Try the room name directly - if not found, you'll get an error with available names to choose from. "
        "Use this when the user wants to control lights in a physical space/room. "
        "This is preferred over individual light control for general commands like 'turn off my lights'."
    )
)
async def turn_off_room(room_name: str) -> ActionResult:
    controller = await RoomController.from_name(room_name)
    return await controller.turn_off()


@mcp.tool(
    description=(
        "Set the brightness of all lights in a room. "
        "Try the room name directly - if not found, you'll get an error with available names to choose from. "
        "Use this when the user wants to control brightness in a physical space/room. "
        "This is preferred over individual light control for general commands like 'make my lights brighter/dimmer'."
    )
)
async def set_room_brightness(room_name: str, percentage: float | int) -> ActionResult:
    controller = await RoomController.from_name(room_name)
    return await controller.set_brightness_percentage(percentage)


@mcp.tool(
    description=(
        "Increase the brightness of all lights in a room. "
        "Try the room name directly - if not found, you'll get an error with available names to choose from. "
        "Use this when the user wants to make lights brighter in a physical space/room. "
        "This is preferred over individual light control for general commands like 'make my lights brighter'."
    )
)
async def increase_room_brightness(
    room_name: str, percentage: float | int
) -> ActionResult:
    controller = await RoomController.from_name(room_name)
    return await controller.increase_brightness_percentage(percentage)


@mcp.tool(
    description=(
        "Decrease the brightness of all lights in a room. "
        "Try the room name directly - if not found, you'll get an error with available names to choose from. "
        "Use this when the user wants to make lights dimmer in a physical space/room. "
        "This is preferred over individual light control for general commands like 'make my lights dimmer'."
    )
)
async def decrease_room_brightness(
    room_name: str, percentage: float | int
) -> ActionResult:
    controller = await RoomController.from_name(room_name)
    return await controller.decrease_brightness_percentage(percentage)


@mcp.tool(
    description=(
        "Set the color temperature of all lights in a room. "
        "Try the room name directly - if not found, you'll get an error with available names to choose from. "
        "Use this when the user wants to control color temperature in a physical space/room."
    )
)
async def set_room_color_temperature(
    room_name: str, percentage: float | int
) -> ActionResult:
    controller = await RoomController.from_name(room_name)
    return await controller.set_color_temperature_percentage(percentage)


@mcp.tool(
    description=(
        "Activate a scene in a room. "
        "Try the room name directly - if not found, you'll get an error with available names to choose from. "
        "Scenes are predefined lighting configurations. Use this to apply lighting presets to a room."
    )
)
async def activate_room_scene(room_name: str, scene_name: str) -> ActionResult:
    controller = await RoomController.from_name(room_name)
    return await controller.activate_scene(scene_name)


# ===== Zones =====


@mcp.tool(
    description=(
        "Discover all available zones. "
        "Zones are logical groupings of lights that can span multiple rooms (e.g., 'Reading Corner', 'Dining Area'). "
        "Use zones when the user refers to controlling lights in a specific logical area or custom grouping."
    )
)
async def discover_zones() -> str:
    zone_lookup = ZoneLookup()
    zones = await zone_lookup.get_all_entities()
    zone_names = [zone.name for zone in zones]
    return "\n".join(zone_names)


@mcp.tool(
    description=(
        "Turn on all lights in a zone. "
        "Try the zone name directly - if not found, you'll get an error with available names to choose from. "
        "Use this when the user wants to control lights in a logical area or custom grouping. "
        "Zones are useful for controlling specific areas that span multiple rooms."
    )
)
async def turn_on_zone(zone_name: str) -> ActionResult:
    controller = await ZoneController.from_name(zone_name)
    return await controller.turn_on()


@mcp.tool(
    description=(
        "Turn off all lights in a zone. "
        "Try the zone name directly - if not found, you'll get an error with available names to choose from. "
        "Use this when the user wants to control lights in a logical area or custom grouping. "
        "Zones are useful for controlling specific areas that span multiple rooms."
    )
)
async def turn_off_zone(zone_name: str) -> ActionResult:
    controller = await ZoneController.from_name(zone_name)
    return await controller.turn_off()


@mcp.tool(
    description=(
        "Set the brightness of all lights in a zone. "
        "Try the zone name directly - if not found, you'll get an error with available names to choose from. "
        "Use this when the user wants to control brightness in a logical area or custom grouping. "
        "Zones allow controlling brightness across multiple rooms as one unit."
    )
)
async def set_zone_brightness(zone_name: str, percentage: float | int) -> ActionResult:
    controller = await ZoneController.from_name(zone_name)
    return await controller.set_brightness_percentage(percentage)


@mcp.tool(
    description=(
        "Increase the brightness of all lights in a zone. "
        "Try the zone name directly - if not found, you'll get an error with available names to choose from. "
        "Use this when the user wants to make lights brighter in a logical area or custom grouping. "
        "Zones allow increasing brightness across multiple rooms simultaneously."
    )
)
async def increase_zone_brightness(
    zone_name: str, percentage: float | int
) -> ActionResult:
    controller = await ZoneController.from_name(zone_name)
    return await controller.increase_brightness_percentage(percentage)


@mcp.tool(
    description=(
        "Decrease the brightness of all lights in a zone. "
        "Try the zone name directly - if not found, you'll get an error with available names to choose from. "
        "Use this when the user wants to make lights dimmer in a logical area or custom grouping. "
        "Zones allow decreasing brightness across multiple rooms simultaneously."
    )
)
async def decrease_zone_brightness(
    zone_name: str, percentage: float | int
) -> ActionResult:
    controller = await ZoneController.from_name(zone_name)
    return await controller.decrease_brightness_percentage(percentage)


@mcp.tool(
    description=(
        "Set the color temperature of all lights in a zone. "
        "Try the zone name directly - if not found, you'll get an error with available names to choose from. "
        "Use this when the user wants to control color temperature in a logical area or custom grouping."
    )
)
async def set_zone_color_temperature(
    zone_name: str, percentage: float | int
) -> ActionResult:
    controller = await ZoneController.from_name(zone_name)
    return await controller.set_color_temperature_percentage(percentage)


@mcp.tool(
    description=(
        "Activate a scene in a zone. "
        "Try the zone name directly - if not found, you'll get an error with available names to choose from. "
        "Scenes are predefined lighting configurations. Use this to apply lighting presets to a zone."
    )
)
async def activate_zone_scene(zone_name: str, scene_name: str) -> ActionResult:
    controller = await ZoneController.from_name(zone_name)
    return await controller.activate_scene(scene_name)


# ===== Scenes =====


@mcp.tool(
    description=(
        "Discover all available scenes. "
        "Scenes are predefined lighting configurations that can be applied to rooms or zones. "
        "Use this to see what lighting presets are available before activating them."
    )
)
async def discover_light_scenes() -> list[ShortSceneInfo]:
    lookup = SceneLookup()
    scenes = await lookup.get_scenes()
    return [ShortSceneInfo.from_scene_info(scene) for scene in scenes]


if __name__ == "__main__":
    mcp.run()
