from typing import Protocol
from uuid import uuid4

import pytest

from hueify.groups.models import GroupArchetype, GroupInfo, GroupMetadata, GroupType
from hueify.lights.models import (
    LightInfo,
    LightMetadata,
)
from hueify.scenes.models import (
    SceneInfo,
    SceneMetadata,
    SceneStatus,
    SceneStatusValue,
)
from hueify.shared.types.resource import (
    DimmingState,
    LightOnState,
    ResourceReference,
    ResourceType,
)


class EntityWithName(Protocol):
    name: str


def create_mock_light(name: str) -> LightInfo:
    return LightInfo(
        id=uuid4(),
        type=ResourceType.LIGHT,
        owner=ResourceReference(rid=uuid4(), rtype=ResourceType.DEVICE),
        metadata=LightMetadata(name=name, archetype=None),
        on=LightOnState(on=False),
        dimming=DimmingState(brightness=50.0),
    )


def create_mock_room(name: str) -> GroupInfo:
    return GroupInfo(
        id=uuid4(),
        type=GroupType.ROOM,
        metadata=GroupMetadata(name=name, archetype=GroupArchetype.LIVING_ROOM),
    )


def create_mock_zone(name: str) -> GroupInfo:
    return GroupInfo(
        id=uuid4(),
        type=GroupType.ZONE,
        metadata=GroupMetadata(name=name, archetype=GroupArchetype.HOME),
    )


def create_mock_scene(name: str) -> SceneInfo:
    return SceneInfo(
        id=uuid4(),
        metadata=SceneMetadata(name=name, image=None),
        group=ResourceReference(rid=uuid4(), rtype=ResourceType.ROOM),
        actions=[],
        status=SceneStatus(active=SceneStatusValue.INACTIVE),
    )


class MockLightLookup:
    async def get_light_names(self) -> list[str]:
        return [
            "Living Room Ceiling",
            "Living Room Floor Lamp",
            "Kitchen Counter",
            "Bedroom Nightstand",
        ]

    async def get_all_entities(self) -> list[LightInfo]:
        return [
            create_mock_light("Living Room Ceiling"),
            create_mock_light("Living Room Floor Lamp"),
            create_mock_light("Kitchen Counter"),
            create_mock_light("Bedroom Nightstand"),
        ]


class MockRoomLookup:
    async def get_all_entities(self) -> list[GroupInfo]:
        return [
            create_mock_room("Living Room"),
            create_mock_room("Kitchen"),
            create_mock_room("Bedroom"),
            create_mock_room("Bathroom"),
        ]


class MockZoneLookup:
    async def get_all_entities(self) -> list[GroupInfo]:
        return [
            create_mock_zone("Downstairs"),
            create_mock_zone("Upstairs"),
        ]


class MockSceneLookup:
    async def get_scenes(self) -> list[SceneInfo]:
        return [
            create_mock_scene("Relax"),
            create_mock_scene("Concentrate"),
            create_mock_scene("Energize"),
            create_mock_scene("Bright"),
        ]

    async def get_all_entities(self) -> list[SceneInfo]:
        return await self.get_scenes()


class MockPromptFileReader:
    def __init__(self, content: str) -> None:
        self._content = content

    def read_prompt_file(self) -> str:
        return self._content


@pytest.fixture
def mock_light_lookup() -> MockLightLookup:
    return MockLightLookup()


@pytest.fixture
def mock_room_lookup() -> MockRoomLookup:
    return MockRoomLookup()


@pytest.fixture
def mock_zone_lookup() -> MockZoneLookup:
    return MockZoneLookup()


@pytest.fixture
def mock_scene_lookup() -> MockSceneLookup:
    return MockSceneLookup()


@pytest.fixture
def mock_file_reader() -> MockPromptFileReader:
    content = """# Hueify Lighting Control Assistant

You are an intelligent Hue lighting control assistant powered by the Hueify MCP Server.

<control-hierarchy>
1. **Rooms**: Physical spaces that group lights together
   - Use for general lighting commands
   - Rooms are the default choice for most user requests

2. **Zones**: Logical groupings that can span multiple rooms
   - Use only when the user explicitly mentions a custom area

3. **Individual Lights**: Specific light fixtures
   - Use only when the user clearly refers to a specific individual light

4. **Scenes**: Predefined lighting configurations
   - Apply preset ambiances to rooms or zones
</control-hierarchy>

<decision-strategy>
1. **Parse intent**: What action do they want?
2. **Identify target type**: Room, Zone, Light, or Scene?
3. **Extract the name** user provided
4. **Call the appropriate tool** with that name
</decision-strategy>

<tool-usage>
- Use the exact names from the available entities below
- Call tools directly with user's requested name
- The system supports fuzzy matching for slight variations
</tool-usage>

<key-principles>
- Always prefer rooms over individual lights for general commands
- Use zones only when explicitly mentioned
- Apply scenes for mood/ambiance requests
- Be conversational and explain what you're doing
</key-principles>

<available-entities>
**Rooms:**
- Living Room
- Kitchen

**Zones:**
- Upstairs

**Lights:**
- Office Light

**Scenes:**
- Relax
</available-entities>"""
    return MockPromptFileReader(content)
