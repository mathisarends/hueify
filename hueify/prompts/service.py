import asyncio
from pathlib import Path

from hueify.groups import RoomLookup, ZoneLookup
from hueify.lights import LightLookup
from hueify.prompts.files import FileSystemPromptReader, PromptFileReader
from hueify.scenes import SceneLookup


class SystemPromptTemplate:
    PROMPT_FILE = Path(__file__).parent / "files" / "system_prompt.md"

    def __init__(
        self,
        light_lookup: LightLookup | None = None,
        room_lookup: RoomLookup | None = None,
        zone_lookup: ZoneLookup | None = None,
        scene_lookup: SceneLookup | None = None,
        file_reader: PromptFileReader | None = None,
    ) -> None:
        self._light_lookup = light_lookup or LightLookup()
        self._room_lookup = room_lookup or RoomLookup()
        self._zone_lookup = zone_lookup or ZoneLookup()
        self._scene_lookup = scene_lookup or SceneLookup()
        self._file_reader = file_reader or FileSystemPromptReader(str(self.PROMPT_FILE))

        self._base_prompt = self._load_base_prompt()
        self._dynamic_context: str | None = None

    def _load_base_prompt(self) -> str:
        content = self._file_reader.read_prompt_file()
        return self._clean_base_prompt(content)

    def _clean_base_prompt(self, content: str) -> str:
        if "<available-entities>" in content:
            start = content.find("<available-entities>")
            end = content.find("</available-entities>") + len("</available-entities>")
            content = content[:start] + content[end:]

        return content.rstrip()

    async def get_system_prompt(self) -> str:
        if self._dynamic_context is None:
            await self.refresh_dynamic_content()

        return f"{self._base_prompt}\n\n<available-entities>\n{self._dynamic_context}\n</available-entities>"

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
