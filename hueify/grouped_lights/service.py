from typing import Self
from uuid import UUID

from hueify.grouped_lights.models import GroupedLightState
from hueify.http import HttpClient
from hueify.utils.logging import LoggingMixin


class GroupedLights(LoggingMixin):
    def __init__(self, state: GroupedLightState) -> None:
        self._state = state

    @classmethod
    async def from_id(cls, id: UUID, client: HttpClient | None = None) -> Self:
        client = client or HttpClient()

        state = await client.get_resource(
            f"grouped_light/{id}", resource_type=GroupedLightState
        )
        return cls(state=state)

    @property
    def state(self) -> GroupedLightState:
        return self._state
