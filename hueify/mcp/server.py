import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastmcp import Context, FastMCP
from fastmcp.utilities.logging import get_logger

from hueify.groups import RoomController, RoomLookup, ZoneController, ZoneLookup
from hueify.lights import LightController, LightLookup
from hueify.prompts.service import SystemPromptTemplate
from hueify.scenes import SceneLookup
from hueify.shared.cache import get_cache
from hueify.shared.controller import ActionResult

to_client_logger = get_logger(name="fastmcp.server.context.to_client")
to_client_logger.setLevel(logging.DEBUG)


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    cache = get_cache()

    light_lookup = LightLookup()
    room_lookup = RoomLookup()
    zone_lookup = ZoneLookup()
    scene_lookup = SceneLookup()

    await asyncio.gather(
        light_lookup.get_lights(),
        room_lookup.get_all_entities(),
        zone_lookup.get_all_entities(),
        scene_lookup.get_scenes(),
    )

    yield

    await cache.clear_all()


mcp = FastMCP("Hueify MCP Server", lifespan=lifespan)


@mcp.tool(
    description=(
        "Refresh the system prompt to update available entities (lights, rooms, zones, scenes). "
        "Use this when you encounter errors suggesting that entity names in the system prompt are outdated, "
        "such as when trying to activate a scene that doesn't exist or control a light that isn't found."
    )
)
async def refresh_system_prompt() -> str:
    system_prompt_service = SystemPromptTemplate()
    await system_prompt_service.refresh_dynamic_content()
    return "System prompt refreshed successfully. All entity lists are now up to date."


@mcp.tool()
async def turn_on_light(light_name: str) -> ActionResult:
    controller = await LightController.from_name(light_name)
    return await controller.turn_on()


@mcp.tool()
async def turn_off_light(light_name: str, ctx: Context) -> ActionResult:
    ctx.info("Turning off light: %s", light_name)
    controller = await LightController.from_name(light_name)
    return await controller.turn_off()


@mcp.tool()
async def set_light_brightness(
    light_name: str, percentage: float | int
) -> ActionResult:
    controller = await LightController.from_name(light_name)
    return await controller.set_brightness_percentage(percentage)


@mcp.tool()
async def increase_light_brightness(
    light_name: str, percentage: float | int
) -> ActionResult:
    controller = await LightController.from_name(light_name)
    return await controller.increase_brightness_percentage(percentage)


@mcp.tool()
async def decrease_light_brightness(
    light_name: str, percentage: float | int
) -> ActionResult:
    controller = await LightController.from_name(light_name)
    return await controller.decrease_brightness_percentage(percentage)


@mcp.tool()
async def set_light_color_temperature(
    light_name: str, percentage: float | int
) -> ActionResult:
    controller = await LightController.from_name(light_name)
    return await controller.set_color_temperature_percentage(percentage)


# ===== Rooms =====


@mcp.tool()
async def turn_on_room(room_name: str) -> ActionResult:
    controller = await RoomController.from_name(room_name)
    return await controller.turn_on()


@mcp.tool()
async def turn_off_room(room_name: str) -> ActionResult:
    controller = await RoomController.from_name(room_name)
    return await controller.turn_off()


@mcp.tool()
async def set_room_brightness(room_name: str, percentage: float | int) -> ActionResult:
    controller = await RoomController.from_name(room_name)
    return await controller.set_brightness_percentage(percentage)


@mcp.tool()
async def increase_room_brightness(
    room_name: str, percentage: float | int
) -> ActionResult:
    controller = await RoomController.from_name(room_name)
    return await controller.increase_brightness_percentage(percentage)


@mcp.tool()
async def decrease_room_brightness(
    room_name: str, percentage: float | int
) -> ActionResult:
    controller = await RoomController.from_name(room_name)
    return await controller.decrease_brightness_percentage(percentage)


@mcp.tool()
async def set_room_color_temperature(
    room_name: str, percentage: float | int
) -> ActionResult:
    controller = await RoomController.from_name(room_name)
    return await controller.set_color_temperature_percentage(percentage)


@mcp.tool()
async def activate_room_scene(room_name: str, scene_name: str) -> ActionResult:
    controller = await RoomController.from_name(room_name)
    return await controller.activate_scene(scene_name)


# ===== Zones =====


@mcp.tool()
async def turn_on_zone(zone_name: str) -> ActionResult:
    controller = await ZoneController.from_name(zone_name)
    return await controller.turn_on()


@mcp.tool()
async def turn_off_zone(zone_name: str) -> ActionResult:
    controller = await ZoneController.from_name(zone_name)
    return await controller.turn_off()


@mcp.tool()
async def set_zone_brightness(zone_name: str, percentage: float | int) -> ActionResult:
    controller = await ZoneController.from_name(zone_name)
    return await controller.set_brightness_percentage(percentage)


@mcp.tool()
async def increase_zone_brightness(
    zone_name: str, percentage: float | int
) -> ActionResult:
    controller = await ZoneController.from_name(zone_name)
    return await controller.increase_brightness_percentage(percentage)


@mcp.tool()
async def decrease_zone_brightness(
    zone_name: str, percentage: float | int
) -> ActionResult:
    controller = await ZoneController.from_name(zone_name)
    return await controller.decrease_brightness_percentage(percentage)


@mcp.tool()
async def set_zone_color_temperature(
    zone_name: str, percentage: float | int
) -> ActionResult:
    controller = await ZoneController.from_name(zone_name)
    return await controller.set_color_temperature_percentage(percentage)


@mcp.tool()
async def activate_zone_scene(zone_name: str, scene_name: str) -> ActionResult:
    controller = await ZoneController.from_name(zone_name)
    return await controller.activate_scene(scene_name)


if __name__ == "__main__":
    mcp.run()
