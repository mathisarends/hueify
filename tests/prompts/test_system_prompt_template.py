import pytest
from conftest import (
    MockLightLookup,
    MockRoomLookup,
    MockSceneLookup,
    MockZoneLookup,
)

from hueify.mcp.prompts import SystemPromptTemplate


@pytest.mark.asyncio
async def test_get_system_prompt_combines_base_and_dynamic_content(
    mock_light_lookup: MockLightLookup,
    mock_room_lookup: MockRoomLookup,
    mock_zone_lookup: MockZoneLookup,
    mock_scene_lookup: MockSceneLookup,
) -> None:
    template = SystemPromptTemplate(
        light_lookup=mock_light_lookup,
        room_lookup=mock_room_lookup,
        zone_lookup=mock_zone_lookup,
        scene_lookup=mock_scene_lookup,
    )

    prompt = await template.get_system_prompt()

    assert "# Hueify Lighting Control Assistant" in prompt
    assert "<available-entities>" in prompt
    assert "</available-entities>" in prompt


@pytest.mark.asyncio
async def test_get_system_prompt_contains_all_entity_types(
    mock_light_lookup: MockLightLookup,
    mock_room_lookup: MockRoomLookup,
    mock_zone_lookup: MockZoneLookup,
    mock_scene_lookup: MockSceneLookup,
) -> None:
    template = SystemPromptTemplate(
        light_lookup=mock_light_lookup,
        room_lookup=mock_room_lookup,
        zone_lookup=mock_zone_lookup,
        scene_lookup=mock_scene_lookup,
    )

    prompt = await template.get_system_prompt()

    assert "**Rooms:**" in prompt
    assert "**Zones:**" in prompt
    assert "**Lights:**" in prompt
    assert "**Scenes:**" in prompt


@pytest.mark.asyncio
async def test_get_system_prompt_includes_entity_names(
    mock_light_lookup: MockLightLookup,
    mock_room_lookup: MockRoomLookup,
    mock_zone_lookup: MockZoneLookup,
    mock_scene_lookup: MockSceneLookup,
) -> None:
    template = SystemPromptTemplate(
        light_lookup=mock_light_lookup,
        room_lookup=mock_room_lookup,
        zone_lookup=mock_zone_lookup,
        scene_lookup=mock_scene_lookup,
    )

    prompt = await template.get_system_prompt()

    assert "- Living Room Ceiling" in prompt
    assert "- Kitchen Counter" in prompt
    assert "- Living Room" in prompt
    assert "- Kitchen" in prompt
    assert "- Bedroom" in prompt
    assert "- Downstairs" in prompt
    assert "- Upstairs" in prompt
    assert "- Relax" in prompt
    assert "- Concentrate" in prompt
    assert "- Energize" in prompt


@pytest.mark.asyncio
async def test_get_system_prompt_has_single_available_entities_section(
    mock_light_lookup: MockLightLookup,
    mock_room_lookup: MockRoomLookup,
    mock_zone_lookup: MockZoneLookup,
    mock_scene_lookup: MockSceneLookup,
) -> None:
    template = SystemPromptTemplate(
        light_lookup=mock_light_lookup,
        room_lookup=mock_room_lookup,
        zone_lookup=mock_zone_lookup,
        scene_lookup=mock_scene_lookup,
    )

    prompt = await template.get_system_prompt()

    opening_count = prompt.count("<available-entities>")
    closing_count = prompt.count("</available-entities>")

    assert opening_count == 1
    assert closing_count == 1


@pytest.mark.asyncio
async def test_refresh_dynamic_content_updates_entities(
    mock_light_lookup: MockLightLookup,
    mock_room_lookup: MockRoomLookup,
    mock_zone_lookup: MockZoneLookup,
    mock_scene_lookup: MockSceneLookup,
) -> None:
    template = SystemPromptTemplate(
        light_lookup=mock_light_lookup,
        room_lookup=mock_room_lookup,
        zone_lookup=mock_zone_lookup,
        scene_lookup=mock_scene_lookup,
    )

    first_prompt = await template.get_system_prompt()
    await template.refresh_dynamic_content()
    second_prompt = await template.get_system_prompt()

    assert first_prompt == second_prompt


@pytest.mark.asyncio
async def test_empty_entity_lists_show_none_available() -> None:
    class EmptyLightLookup:
        async def get_light_names(self) -> list[str]:
            return []

        async def get_all_entities(self) -> list:
            return []

    class EmptyGroupLookup:
        async def get_all_entities(self) -> list:
            return []

    class EmptySceneLookup:
        async def get_scenes(self) -> list:
            return []

        async def get_all_entities(self) -> list:
            return []

    template = SystemPromptTemplate(
        light_lookup=EmptyLightLookup(),
        room_lookup=EmptyGroupLookup(),
        zone_lookup=EmptyGroupLookup(),
        scene_lookup=EmptySceneLookup(),
    )

    prompt = await template.get_system_prompt()

    assert "- None available" in prompt
