from hueify.grouped_lights import RoomNamespace, ZoneNamespace
from hueify.light import LightNamespace


class SystemPromptTemplate:
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

    def __init__(
        self,
        lights: LightNamespace,
        rooms: RoomNamespace,
        zones: ZoneNamespace,
    ) -> None:
        self._lights = lights
        self._rooms = rooms
        self._zones = zones

    def render(self) -> str:
        dynamic_context = self._build_dynamic_context(
            lights=self._lights.names,
            rooms=self._rooms.names,
            zones=self._zones.names,
            scenes=self._collect_all_scene_names(),
        )
        return f"{self._BASE_PROMPT}\n\n<available-entities>\n{dynamic_context}\n</available-entities>"

    def _collect_all_scene_names(self) -> list[str]:
        seen: set[str] = set()
        for room_name in self._rooms.names:
            for scene_name in self._rooms.scene_names(room_name):
                seen.add(scene_name)
        return sorted(seen)

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
