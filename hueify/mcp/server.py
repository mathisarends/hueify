from hueify import ActionResult
from hueify.grouped_lights import RoomNamespace, ZoneNamespace
from hueify.light import LightNamespace
from hueify.mcp.app import HueifyMCP, lifespan

mcp_server = HueifyMCP("Hueify MCP Server", lifespan=lifespan)


# ===== Lights =====


@mcp_server.light_tool()
async def turn_on_light(light_name: str, lights: LightNamespace) -> ActionResult:
    light = lights.from_name(light_name)
    return await light.turn_on()


@mcp_server.light_tool()
async def turn_off_light(light_name: str, lights: LightNamespace) -> ActionResult:
    light = lights.from_name(light_name)
    return await light.turn_off()


@mcp_server.light_tool()
async def set_light_brightness(
    light_name: str, percentage: float, lights: LightNamespace
) -> ActionResult:
    light = lights.from_name(light_name)
    return await light.set_brightness(percentage)


@mcp_server.light_tool()
async def increase_light_brightness(
    light_name: str, percentage: float, lights: LightNamespace
) -> ActionResult:
    light = lights.from_name(light_name)
    return await light.increase_brightness(percentage)


@mcp_server.light_tool()
async def decrease_light_brightness(
    light_name: str, percentage: float, lights: LightNamespace
) -> ActionResult:
    light = lights.from_name(light_name)
    return await light.decrease_brightness(percentage)


@mcp_server.light_tool()
async def set_light_color_temperature(
    light_name: str, percentage: float, lights: LightNamespace
) -> ActionResult:
    light = lights.from_name(light_name)
    return await light.set_color_temperature(percentage)


@mcp_server.light_tool()
async def get_light_brightness(light_name: str, lights: LightNamespace) -> float:
    light = lights.from_name(light_name)
    return light.brightness_percentage


# ===== Rooms =====


@mcp_server.room_tool()
async def turn_on_room(room_name: str, rooms: RoomNamespace) -> ActionResult:
    room = rooms.from_name(room_name)
    return await room.turn_on()


@mcp_server.room_tool()
async def turn_off_room(room_name: str, rooms: RoomNamespace) -> ActionResult:
    room = rooms.from_name(room_name)
    return await room.turn_off()


@mcp_server.room_tool()
async def set_room_brightness(
    room_name: str, percentage: float, rooms: RoomNamespace
) -> ActionResult:
    room = rooms.from_name(room_name)
    return await room.set_brightness(percentage)


@mcp_server.room_tool()
async def increase_room_brightness(
    room_name: str, percentage: float, rooms: RoomNamespace
) -> ActionResult:
    room = rooms.from_name(room_name)
    return await room.increase_brightness(percentage)


@mcp_server.room_tool()
async def decrease_room_brightness(
    room_name: str, percentage: float, rooms: RoomNamespace
) -> ActionResult:
    room = rooms.from_name(room_name)
    return await room.decrease_brightness(percentage)


@mcp_server.room_tool()
async def set_room_color_temperature(
    room_name: str, percentage: float, rooms: RoomNamespace
) -> ActionResult:
    room = rooms.from_name(room_name)
    return await room.set_color_temperature(percentage)


@mcp_server.room_tool()
async def get_room_brightness(room_name: str, rooms: RoomNamespace) -> float:
    room = rooms.from_name(room_name)
    return room.brightness_percentage


@mcp_server.room_tool()
async def activate_scene_in_room(
    room_name: str, scene_name: str, rooms: RoomNamespace
) -> ActionResult:
    room = rooms.from_name(room_name)
    return await room.activate_scene(scene_name)


@mcp_server.room_tool()
async def get_active_scene_in_room(room_name: str, rooms: RoomNamespace) -> str:
    room = rooms.from_name(room_name)
    active_scene = room.get_active_scene()
    return (
        f"Active scene: '{active_scene.name}'"
        if active_scene
        else f"No active scene in '{room_name}'"
    )


@mcp_server.room_tool()
async def list_scenes_in_room(room_name: str, rooms: RoomNamespace) -> list[str]:
    room = rooms.from_name(room_name)
    return room.scene_names


# ===== Zones =====


@mcp_server.zone_tool()
async def turn_on_zone(zone_name: str, zones: ZoneNamespace) -> ActionResult:
    zone = zones.from_name(zone_name)
    return await zone.turn_on()


@mcp_server.zone_tool()
async def turn_off_zone(zone_name: str, zones: ZoneNamespace) -> ActionResult:
    zone = zones.from_name(zone_name)
    return await zone.turn_off()


@mcp_server.zone_tool()
async def set_zone_brightness(
    zone_name: str, percentage: float, zones: ZoneNamespace
) -> ActionResult:
    zone = zones.from_name(zone_name)
    return await zone.set_brightness(percentage)


@mcp_server.zone_tool()
async def increase_zone_brightness(
    zone_name: str, percentage: float, zones: ZoneNamespace
) -> ActionResult:
    zone = zones.from_name(zone_name)
    return await zone.increase_brightness(percentage)


@mcp_server.zone_tool()
async def decrease_zone_brightness(
    zone_name: str, percentage: float, zones: ZoneNamespace
) -> ActionResult:
    zone = zones.from_name(zone_name)
    return await zone.decrease_brightness(percentage)


@mcp_server.zone_tool()
async def set_zone_color_temperature(
    zone_name: str, percentage: float, zones: ZoneNamespace
) -> ActionResult:
    zone = zones.from_name(zone_name)
    return await zone.set_color_temperature(percentage)


@mcp_server.zone_tool()
async def get_zone_brightness(zone_name: str, zones: ZoneNamespace) -> float:
    zone = zones.from_name(zone_name)
    return zone.brightness_percentage


@mcp_server.zone_tool()
async def activate_scene_in_zone(
    zone_name: str, scene_name: str, zones: ZoneNamespace
) -> ActionResult:
    zone = zones.from_name(zone_name)
    return await zone.activate_scene(scene_name)


@mcp_server.zone_tool()
async def get_active_scene_in_zone(zone_name: str, zones: ZoneNamespace) -> str:
    zone = zones.from_name(zone_name)
    active_scene = zone.get_active_scene()
    return (
        f"Active scene: '{active_scene.name}'"
        if active_scene
        else f"No active scene in '{zone_name}'"
    )


@mcp_server.zone_tool()
async def list_scenes_in_zone(zone_name: str, zones: ZoneNamespace) -> list[str]:
    zone = zones.from_name(zone_name)
    return zone.scene_names


if __name__ == "__main__":
    mcp_server.run()
