import pytest

from hueify.prompts.service import SystemPromptTemplate


class TestSystemPromptTemplate:
    @pytest.mark.asyncio
    async def test_get_system_prompt_contains_all_sections(self):
        template = SystemPromptTemplate()
        prompt = await template.get_system_prompt()

        assert "# Hueify Lighting Control Assistant" in prompt
        assert "## Control Hierarchy" in prompt
        assert "## Decision Strategy" in prompt
        assert "## Tool Usage" in prompt
        assert "## Key Principles" in prompt
        assert "## Available Entities" in prompt

    @pytest.mark.asyncio
    async def test_get_system_prompt_contains_entity_types(self):
        template = SystemPromptTemplate()
        prompt = await template.get_system_prompt()

        assert "**Rooms:**" in prompt
        assert "**Zones:**" in prompt
        assert "**Lights:**" in prompt
        assert "**Scenes:**" in prompt

    @pytest.mark.asyncio
    async def test_get_system_prompt_no_placeholder_text(self):
        template = SystemPromptTemplate()
        prompt = await template.get_system_prompt()

        assert "{rooms will be injected here}" not in prompt
        assert "{zones will be injected here}" not in prompt
        assert "{lights will be injected here}" not in prompt
        assert "{scenes will be injected here}" not in prompt

    @pytest.mark.asyncio
    async def test_get_system_prompt_only_one_available_entities_section(self):
        template = SystemPromptTemplate()
        prompt = await template.get_system_prompt()

        count = prompt.count("## Available Entities")
        assert count == 1, f"Expected 1 'Available Entities' section, found {count}"

    @pytest.mark.asyncio
    async def test_refresh_dynamic_content_updates_entities(self):
        template = SystemPromptTemplate()

        first_prompt = await template.get_system_prompt()

        await template.refresh_dynamic_content()

        second_prompt = await template.get_system_prompt()

        assert first_prompt == second_prompt

    @pytest.mark.asyncio
    async def test_dynamic_context_has_list_items(self):
        template = SystemPromptTemplate()
        prompt = await template.get_system_prompt()

        entities_section = prompt.split("## Available Entities")[1]

        assert "- " in entities_section

    @pytest.mark.asyncio
    async def test_system_prompt_contains_scene_section_at_end(self):
        template = SystemPromptTemplate()
        prompt = await template.get_system_prompt()

        entities_section = prompt.split("## Available Entities")[1]

        assert "**Scenes:**" in entities_section
        scenes_index = entities_section.find("**Scenes:**")
        assert scenes_index > 0
