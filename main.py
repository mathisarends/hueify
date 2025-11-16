import asyncio
from pathlib import Path

from agents import Agent, Runner, SQLiteSession
from agents.mcp import MCPServerStdio
from dotenv import load_dotenv

from hueify.prompts.service import SystemPromptTemplate

load_dotenv(override=True)

HUEIFY_DIR = Path("c:/code/hueify")


async def main():
    system_prompt_service = SystemPromptTemplate()
    system_prompt = await system_prompt_service.get_system_prompt()

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
            name=server.name,
            instructions=system_prompt,
            mcp_servers=[server],
            model="gpt-4.1-mini",
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
