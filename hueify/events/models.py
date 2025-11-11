from enum import StrEnum
from typing import Self
from uuid import UUID

from pydantic import BaseModel


class ResourceType(StrEnum):
    LIGHT = "light"
    GROUPED_LIGHT = "grouped_light"
    BUTTON = "button"
    MOTION = "motion"
    TEMPERATURE = "temperature"
    RELATIVE_ROTARY = "relative_rotary"
    SCENE = "scene"
    ROOM = "room"
    ZONE = "zone"
    # ... add more as needed


class EventType(StrEnum):
    UPDATE = "update"
    ADD = "add"
    DELETE = "delete"


# TODO: Use DU for this here
class ResourceData(BaseModel):
    id: UUID
    type: str


class EventData(BaseModel):
    creationtime: str
    data: list[ResourceData]
    id: UUID
    type: EventType


class Event(BaseModel):
    events: list[EventData]

    @classmethod
    def from_sse_data(cls, sse_data_list: list[dict]) -> Self:
        return cls(events=sse_data_list)
