import asyncio

from hueify.groups import RoomLookup, ZoneLookup
from hueify.lights import LightLookup
from hueify.scenes import SceneLookup

_BASE_PROMPT = """# Hueify Lighting Control Assistant

You are an intelligent Hue lighting control assistant powered by the Hueify MCP Server.

<control-hierarchy>
1. **Rooms**: Physical spaces that group lights together
   - Use for general lighting commands: "turn on my lights", "make it brighter", "dim the lights"
   - Rooms are the default choice for most user requests

2. **Zones**: Logical groupings that can span multiple rooms
   - Use only when the user explicitly mentions a custom area or logical grouping

3. **Individual Lights**: Specific light fixtures
   - Use only when the user clearly refers to a specific individual light
   - Prefer rooms over individual lights for general commands

4. **Scenes**: Predefined lighting configurations
   - Apply preset ambiances to rooms or zones
   - Use when user requests mood-based lighting
</control-hierarchy>

<decision-strategy>
1. **Parse intent**: What action do they want? (on/off, brightness, scene, color temperature)
2. **Identify target type**: Room, Zone, Light, or Scene?
3. **Extract the name** user provided
4. **Call the appropriate tool** with that name
</decision-strategy>

<tool-usage>
- Use the exact names from the available entities below
- Call tools directly with user's requested name
- The system supports fuzzy matching for slight variations
- When user requests mood/ambiance, first discover available scenes, then apply
</tool-usage>

<key-principles>
- Always prefer rooms over individual lights for general commands
- Use zones only when explicitly mentioned
- Apply scenes for mood/ambiance requests
- Be conversational and explain what you're doing
</key-principles>"""


class SystemPromptTemplate:
    def __init__(
        self,
        light_lookup: LightLookup | None = None,
        room_lookup: RoomLookup | None = None,
        zone_lookup: ZoneLookup | None = None,
        scene_lookup: SceneLookup | None = None,
    ) -> None:
        self._light_lookup = light_lookup or LightLookup()
        self._room_lookup = room_lookup or RoomLookup()
        self._zone_lookup = zone_lookup or ZoneLookup()
        self._scene_lookup = scene_lookup or SceneLookup()
        self._dynamic_context: str | None = None

    async def get_system_prompt(self) -> str:
        if self._dynamic_context is None:
            await self.refresh_dynamic_content()

        return f"{_BASE_PROMPT}\n\n<available-entities>\n{self._dynamic_context}\n</available-entities>"

    async def refresh_dynamic_content(self) -> None:
        lights_task = self._light_lookup.get_light_names()
        rooms_task = self._room_lookup.get_all_entities()
        zones_task = self._zone_lookup.get_all_entities()
        scenes_task = self._scene_lookup.get_scenes()

        lights, rooms, zones, scenes = await asyncio.gather(
            lights_task, rooms_task, zones_task, scenes_task
        )

        room_names = [room.name for room in rooms]
        zone_names = [zone.name for zone in zones]
        scene_names = [scene.name for scene in scenes]

        self._dynamic_context = self._build_dynamic_context(
            lights=lights,
            rooms=room_names,
            zones=zone_names,
            scenes=scene_names,
        )

    def _build_dynamic_context(
        self,
        lights: list[str],
        rooms: list[str],
        zones: list[str],
        scenes: list[str],
    ) -> str:
        return (
            "**Rooms:**\n"
            f"{self._format_list(rooms)}\n\n"
            "**Zones:**\n"
            f"{self._format_list(zones)}\n\n"
            "**Lights:**\n"
            f"{self._format_list(lights)}\n\n"
            "**Scenes:**\n"
            f"{self._format_list(scenes)}"
        )

    def _format_list(self, items: list[str]) -> str:
        if not items:
            return "- None available"
        return "\n".join(f"- {item}" for item in items)
