from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Self
from uuid import UUID

from hueify.grouped_lights import GroupedLights
from hueify.groups.models import GroupInfo
from hueify.http import HttpClient
from hueify.shared.resource.models import (
    ActionResult,
)

if TYPE_CHECKING:
    from hueify.shared.resource import NamedResourceLookup


class Group:
    def __init__(
        self,
        group_info: GroupInfo,
        grouped_lights: GroupedLights,
        client: HttpClient | None = None,
    ) -> None:
        self._group_info = group_info
        self._grouped_lights = grouped_lights
        self._client = client or HttpClient()

    @classmethod
    async def from_name(cls, group_name: str, client: HttpClient | None = None) -> Self:
        client = client or HttpClient()
        group_lookup = cls._create_lookup(client)
        group_info = await group_lookup.get_entity_by_name(group_name)

        grouped_light_id = cls._extract_grouped_light_id(group_info)
        grouped_lights = await GroupedLights.from_id(grouped_light_id, client=client)
        return cls(group_info=group_info, grouped_lights=grouped_lights, client=client)

    @staticmethod
    def _extract_grouped_light_id(group_info: GroupInfo) -> UUID:
        grouped_light_reference = group_info.get_grouped_light_reference_if_exists()

        if grouped_light_reference is None:
            raise ValueError(
                f"No grouped_light service found for group {group_info.id}"
            )

        return grouped_light_reference

    @classmethod
    @abstractmethod
    def _create_lookup(cls, client: HttpClient) -> NamedResourceLookup:
        pass

    @property
    def id(self) -> UUID:
        return self._group_info.id

    @property
    def name(self) -> str:
        return self._group_info.name

    @property
    def grouped_light_id(self) -> UUID:
        return self._grouped_lights.id

    @property
    def is_on(self) -> bool:
        return self._grouped_lights.is_on

    @property
    def brightness_percentage(self) -> float:
        return self._grouped_lights.brightness_percentage

    @property
    def color_temperature_percentage(self) -> int | None:
        return self._grouped_lights.color_temperature_percentage

    async def turn_on(self) -> ActionResult:
        return await self._grouped_lights.turn_on()

    async def turn_off(self) -> ActionResult:
        return await self._grouped_lights.turn_off()

    async def set_brightness(self, percentage: float | int) -> ActionResult:
        return await self._grouped_lights.set_brightness(percentage)

    async def increase_brightness(self, percentage: float | int) -> ActionResult:
        return await self._grouped_lights.increase_brightness(percentage)

    async def decrease_brightness(self, percentage: float | int) -> ActionResult:
        return await self._grouped_lights.decrease_brightness(percentage)

    async def set_color_temperature(self, percentage: float | int) -> ActionResult:
        return await self._grouped_lights.set_color_temperature(percentage)
