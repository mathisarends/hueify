from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastmcp import FastMCP

from hueify.groups import Room, Zone
from hueify.lights import Light
from hueify.prompts import SystemPromptTemplate
from hueify.shared.cache import get_cache
from hueify.shared.resource import ActionResult


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    cache = get_cache()
    await cache.populate()

    yield

    await cache.clear_all()


mcp_server = FastMCP("Hueify MCP Server", lifespan=lifespan)


@mcp_server.tool(
    description=(
        "Refresh the system prompt to update available entities (lights, rooms, zones, scenes). "
        "Use this when you encounter errors suggesting that entity names in the system prompt are outdated, "
        "such as when trying to activate a scene that doesn't exist or control a light that isn't found."
    )
)
async def refresh_system_prompt() -> str:
    cache = get_cache()
    await cache.clear_all()

    system_prompt_service = SystemPromptTemplate()
    await system_prompt_service.refresh_dynamic_content()
    return "System prompt refreshed successfully. All entity lists are now up to date."


@mcp_server.tool()
async def turn_on_light(light_name: str) -> ActionResult:
    light = await Light.from_name(light_name)
    return await light.turn_on()


@mcp_server.tool()
async def turn_off_light(light_name: str) -> ActionResult:
    light = await Light.from_name(light_name)
    return await light.turn_off()


@mcp_server.tool()
async def set_light_brightness(
    light_name: str, percentage: float | int
) -> ActionResult:
    light = await Light.from_name(light_name)
    return await light.set_brightness_percentage(percentage)


@mcp_server.tool()
async def increase_light_brightness(
    light_name: str, percentage: float | int
) -> ActionResult:
    light = await Light.from_name(light_name)
    return await light.increase_brightness_percentage(percentage)


@mcp_server.tool()
async def decrease_light_brightness(
    light_name: str, percentage: float | int
) -> ActionResult:
    light = await Light.from_name(light_name)
    return await light.decrease_brightness_percentage(percentage)


@mcp_server.tool()
async def set_light_color_temperature(
    light_name: str, percentage: float | int
) -> ActionResult:
    light = await Light.from_name(light_name)
    return await light.set_color_temperature_percentage(percentage)


@mcp_server.tool()
async def get_light_brightness_percentage(light_name: str) -> float:
    light = await Light.from_name(light_name)
    return light.brightness_percentage


@mcp_server.tool()
async def get_room_brightness_percentage(room_name: str) -> float:
    room = await Room.from_name(room_name)
    return room.brightness_percentage


@mcp_server.tool()
async def get_zone_brightness_percentage(zone_name: str) -> float:
    zone = await Zone.from_name(zone_name)
    return zone.brightness_percentage


# ===== Rooms =====


@mcp_server.tool()
async def turn_on_room(room_name: str) -> ActionResult:
    room = await Room.from_name(room_name)
    return await room.turn_on()


@mcp_server.tool()
async def turn_off_room(room_name: str) -> ActionResult:
    room = await Room.from_name(room_name)
    return await room.turn_off()


@mcp_server.tool()
async def set_room_brightness(room_name: str, percentage: float | int) -> ActionResult:
    room = await Room.from_name(room_name)
    return await room.set_brightness_percentage(percentage)


@mcp_server.tool()
async def increase_room_brightness(
    room_name: str, percentage: float | int
) -> ActionResult:
    room = await Room.from_name(room_name)
    return await room.increase_brightness_percentage(percentage)


@mcp_server.tool()
async def decrease_room_brightness(
    room_name: str, percentage: float | int
) -> ActionResult:
    room = await Room.from_name(room_name)
    return await room.decrease_brightness_percentage(percentage)


@mcp_server.tool()
async def set_room_color_temperature(
    room_name: str, percentage: float | int
) -> ActionResult:
    room = await Room.from_name(room_name)
    return await room.set_color_temperature_percentage(percentage)


@mcp_server.tool()
async def activate_room_scene(room_name: str, scene_name: str) -> ActionResult:
    room = await Room.from_name(room_name)
    return await room.activate_scene(scene_name)


# ===== Zones =====


@mcp_server.tool()
async def turn_on_zone(zone_name: str) -> ActionResult:
    zone = await Zone.from_name(zone_name)
    return await zone.turn_on()


@mcp_server.tool()
async def turn_off_zone(zone_name: str) -> ActionResult:
    zone = await Zone.from_name(zone_name)
    return await zone.turn_off()


@mcp_server.tool()
async def set_zone_brightness(zone_name: str, percentage: float | int) -> ActionResult:
    zone = await Zone.from_name(zone_name)
    return await zone.set_brightness_percentage(percentage)


@mcp_server.tool()
async def increase_zone_brightness(
    zone_name: str, percentage: float | int
) -> ActionResult:
    zone = await Zone.from_name(zone_name)
    return await zone.increase_brightness_percentage(percentage)


@mcp_server.tool()
async def decrease_zone_brightness(
    zone_name: str, percentage: float | int
) -> ActionResult:
    zone = await Zone.from_name(zone_name)
    return await zone.decrease_brightness_percentage(percentage)


@mcp_server.tool()
async def set_zone_color_temperature(
    zone_name: str, percentage: float | int
) -> ActionResult:
    zone = await Zone.from_name(zone_name)
    return await zone.set_color_temperature_percentage(percentage)


@mcp_server.tool()
async def activate_zone_scene(zone_name: str, scene_name: str) -> ActionResult:
    zone = await Zone.from_name(zone_name)
    return await zone.activate_scene(scene_name)


if __name__ == "__main__":
    mcp_server.run()
