import asyncio
from pathlib import Path

from agents import Agent, Runner
from agents.mcp import MCPServerStdio
from dotenv import load_dotenv

load_dotenv(override=True)

HUEIFY_DIR = Path("c:/code/hueify")


async def main():
    async with MCPServerStdio(
        params={
            "command": "uv",
            "args": [
                "--directory",
                str(HUEIFY_DIR),
                "run",
                "python",
                "-m",
                "hueify.mcp.server",
            ],
        },
        name="My MCP Server",
    ) as server:
        agent = Agent(
            name="Light toggler",
            instructions=(
                "You like to toggle lights using the turn_on_light and turn_off_light tools from the MCP server. "
                "Not More not less. My name is Alex."
            ),
            mcp_servers=[server],
            model="gpt-4.1-mini",
        )

        runner = Runner()
        result = await runner.run(
            starting_agent=agent,
            input="Turn on Lighstripe 1. If the name is not correct, first discover the lights and use the correct name to turn off the light.",
        )

        for step in result.new_items:
            print(step)

        print("result", result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
