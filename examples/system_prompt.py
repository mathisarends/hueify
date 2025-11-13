from hueify import SystemPromptTemplate


async def main():
    prompt = await SystemPromptTemplate().get_system_prompt()
    print(prompt)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
