from fastmcp import FastMCP

from hueify import ActionResult, LightController, LightLookup

mcp = FastMCP("Hueify MCP Server")


@mcp.tool
async def discover_lights() -> list[str]:
    lookup = LightLookup()
    return await lookup.get_light_names()


@mcp.tool
async def turn_on_light(light_name: str) -> ActionResult:
    light_controller = await LightController.from_name(light_name)
    return await light_controller.turn_on()


@mcp.tool
async def turn_off_light(light_name: str) -> ActionResult:
    light_controller = await LightController.from_name(light_name)
    return await light_controller.turn_off()


if __name__ == "__main__":
    mcp.run()
