from enum import StrEnum
from typing import Self
from uuid import UUID

from pydantic import BaseModel, Field


class EventType(StrEnum):
    UPDATE = "update"
    ADD = "add"
    DELETE = "delete"


class ButtonEvent(StrEnum):
    INITIAL_PRESS = "initial_press"
    REPEAT = "repeat"
    SHORT_RELEASE = "short_release"
    LONG_RELEASE = "long_release"
    DOUBLE_SHORT_RELEASE = "double_short_release"


class RotaryAction(StrEnum):
    START = "start"
    REPEAT = "repeat"


class RotaryDirection(StrEnum):
    CLOCK_WISE = "clock_wise"
    COUNTER_CLOCK_WISE = "counter_clock_wise"


class OwnerReference(BaseModel):
    rid: UUID
    rtype: str


class ButtonReport(BaseModel):
    event: ButtonEvent
    updated: str


class ButtonData(BaseModel):
    button_report: ButtonReport
    last_event: ButtonEvent


class OnState(BaseModel):
    on: bool


class DimmingState(BaseModel):
    brightness: float


class ColorXY(BaseModel):
    x: float
    y: float


class ColorState(BaseModel):
    xy: ColorXY


class ColorTemperature(BaseModel):
    mirek: int | None
    mirek_valid: bool


class RotationData(BaseModel):
    direction: RotaryDirection
    duration: int
    steps: int


class RotaryEvent(BaseModel):
    action: RotaryAction
    rotation: RotationData


class RelativeRotaryData(BaseModel):
    last_event: RotaryEvent
    rotary_report: RotaryEvent


class MotionData(BaseModel):
    motion: bool = Field(alias="motion_valid")
    motion_valid: bool | None = None


class SceneStatus(BaseModel):
    active: str
    last_recall: str | None = None


class ResourceData(BaseModel):
    id: UUID
    type: str
    id_v1: str | None = None
    owner: OwnerReference | None = None
    service_id: int | None = None

    button: ButtonData | None = None
    on: OnState | None = None
    dimming: DimmingState | None = None
    color: ColorState | None = None
    color_temperature: ColorTemperature | None = None
    relative_rotary: RelativeRotaryData | None = None
    motion: MotionData | None = None
    status: SceneStatus | None = None


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
