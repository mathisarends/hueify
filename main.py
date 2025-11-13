import asyncio
from pathlib import Path

from agents import Agent, Runner, SQLiteSession
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
            name="Hue Controller",
            instructions=(
                "You are an intelligent assistant that helps users control their Hue lights. "
            ),
            mcp_servers=[server],
            model="gpt-4.1",
        )

        runner = Runner()
        session = SQLiteSession("hue_light_session")  # ← SQLiteSession erstellen!

        print("🔦 Light Control Chat (type 'quit' to exit)")
        print("-" * 50)

        while True:
            user_input = input("\nYou: ").strip()

            if user_input.lower() in ["quit", "exit"]:
                print("\n👋 Goodbye!")
                break

            if not user_input:
                continue

            print("\n⏳ Processing...")
            result = await runner.run(
                starting_agent=agent,
                input=user_input,
                session=session,  # ← Session übergeben!
            )

            print("\n📋 Steps:")
            for step in result.new_items:
                print(f"  {step}")

            print(f"\n🤖 Agent: {result.final_output}")


if __name__ == "__main__":
    asyncio.run(main())
