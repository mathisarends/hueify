from hueify.light import LightNamespace
from hueify.mcp.app import HueifyMCP, lifespan
from hueify.room import RoomNamespace
from hueify.scenes import SceneNamespace
from hueify.shared.resource import ActionResult
from hueify.zone import ZoneNamespace

mcp_server = HueifyMCP("Hueify MCP Server", lifespan=lifespan)


@mcp_server.light_tool()
async def turn_on_light(light_name: str, lights: LightNamespace) -> ActionResult:
    return await lights.turn_on(light_name)


@mcp_server.light_tool()
async def turn_off_light(light_name: str, lights: LightNamespace) -> ActionResult:
    return await lights.turn_off(light_name)


@mcp_server.light_tool()
async def set_light_brightness(
    light_name: str, percentage: float, lights: LightNamespace
) -> ActionResult:
    return await lights.set_brightness(light_name, percentage)


@mcp_server.light_tool()
async def increase_light_brightness(
    light_name: str, percentage: float, lights: LightNamespace
) -> ActionResult:
    return await lights.increase_brightness(light_name, percentage)


@mcp_server.light_tool()
async def decrease_light_brightness(
    light_name: str, percentage: float, lights: LightNamespace
) -> ActionResult:
    return await lights.decrease_brightness(light_name, percentage)


@mcp_server.light_tool()
async def set_light_color_temperature(
    light_name: str, percentage: float, lights: LightNamespace
) -> ActionResult:
    return await lights.set_color_temperature(light_name, percentage)


@mcp_server.light_tool()
async def get_light_brightness(light_name: str, lights: LightNamespace) -> float:
    return await lights.get_brightness(light_name)


# ===== Rooms =====


@mcp_server.room_tool()
async def turn_on_room(room_name: str, rooms: RoomNamespace) -> ActionResult:
    return await rooms.turn_on(room_name)


@mcp_server.room_tool()
async def turn_off_room(room_name: str, rooms: RoomNamespace) -> ActionResult:
    return await rooms.turn_off(room_name)


@mcp_server.room_tool()
async def set_room_brightness(
    room_name: str, percentage: float, rooms: RoomNamespace
) -> ActionResult:
    return await rooms.set_brightness(room_name, percentage)


@mcp_server.room_tool()
async def increase_room_brightness(
    room_name: str, percentage: float, rooms: RoomNamespace
) -> ActionResult:
    return await rooms.increase_brightness(room_name, percentage)


@mcp_server.room_tool()
async def decrease_room_brightness(
    room_name: str, percentage: float, rooms: RoomNamespace
) -> ActionResult:
    return await rooms.decrease_brightness(room_name, percentage)


@mcp_server.room_tool()
async def set_room_color_temperature(
    room_name: str, percentage: float, rooms: RoomNamespace
) -> ActionResult:
    return await rooms.set_color_temperature(room_name, percentage)


@mcp_server.room_tool()
async def get_room_brightness(room_name: str, rooms: RoomNamespace) -> float:
    return await rooms.get_brightness(room_name)


# ===== Zones =====


@mcp_server.zone_tool()
async def turn_on_zone(zone_name: str, zones: ZoneNamespace) -> ActionResult:
    return await zones.turn_on(zone_name)


@mcp_server.zone_tool()
async def turn_off_zone(zone_name: str, zones: ZoneNamespace) -> ActionResult:
    return await zones.turn_off(zone_name)


@mcp_server.zone_tool()
async def set_zone_brightness(
    zone_name: str, percentage: float, zones: ZoneNamespace
) -> ActionResult:
    return await zones.set_brightness(zone_name, percentage)


@mcp_server.zone_tool()
async def increase_zone_brightness(
    zone_name: str, percentage: float, zones: ZoneNamespace
) -> ActionResult:
    return await zones.increase_brightness(zone_name, percentage)


@mcp_server.zone_tool()
async def decrease_zone_brightness(
    zone_name: str, percentage: float, zones: ZoneNamespace
) -> ActionResult:
    return await zones.decrease_brightness(zone_name, percentage)


@mcp_server.zone_tool()
async def set_zone_color_temperature(
    zone_name: str, percentage: float, zones: ZoneNamespace
) -> ActionResult:
    return await zones.set_color_temperature(zone_name, percentage)


@mcp_server.zone_tool()
async def get_zone_brightness(zone_name: str, zones: ZoneNamespace) -> float:
    return await zones.get_brightness(zone_name)


# ===== Scenes =====


@mcp_server.scene_tool()
async def activate_scene_in_room(
    scene_name: str, room_name: str, scenes: SceneNamespace
) -> ActionResult:
    return await scenes.activate_in_room(scene_name, room_name)


@mcp_server.scene_tool()
async def activate_scene_in_zone(
    scene_name: str, zone_name: str, scenes: SceneNamespace
) -> ActionResult:
    return await scenes.activate_in_zone(scene_name, zone_name)


@mcp_server.scene_tool()
async def get_active_scene_in_room(room_name: str, scenes: SceneNamespace) -> str:
    active_scene = scenes.get_active_scene_for_room(room_name)
    return (
        f"Active scene: '{active_scene.name}'"
        if active_scene
        else f"No active scene in '{room_name}'"
    )


@mcp_server.scene_tool()
async def get_active_scene_in_zone(zone_name: str, scenes: SceneNamespace) -> str:
    active_scene = scenes.get_active_scene_for_zone(zone_name)
    return (
        f"Active scene: '{active_scene.name}'"
        if active_scene
        else f"No active scene in '{zone_name}'"
    )


@mcp_server.scene_tool()
async def list_scenes_in_room(room_name: str, scenes: SceneNamespace) -> list[str]:
    return [s.name for s in scenes.list_scenes_for_room(room_name)]


@mcp_server.scene_tool()
async def list_scenes_in_zone(zone_name: str, scenes: SceneNamespace) -> list[str]:
    return [s.name for s in scenes.list_scenes_for_zone(zone_name)]


if __name__ == "__main__":
    mcp_server.run()
