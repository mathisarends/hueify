from enum import StrEnum
from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import BaseModel, Field

from hueify.shared.types import ResourceType


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


class ButtonResource(BaseModel):
    type: Literal[ResourceType.BUTTON] = ResourceType.BUTTON
    id: UUID
    id_v1: str | None = None
    owner: OwnerReference
    button: ButtonData


class RelativeRotaryResource(BaseModel):
    type: Literal[ResourceType.RELATIVE_ROTARY] = ResourceType.RELATIVE_ROTARY
    id: UUID
    id_v1: str | None = None
    owner: OwnerReference
    relative_rotary: RelativeRotaryData


class LightResource(BaseModel):
    type: Literal[ResourceType.LIGHT] = ResourceType.LIGHT
    id: UUID
    id_v1: str | None = None
    owner: OwnerReference
    service_id: int | None = None
    on: OnState | None = None
    dimming: DimmingState | None = None
    color: ColorState | None = None
    color_temperature: ColorTemperature | None = None


class MotionResource(BaseModel):
    type: Literal[ResourceType.MOTION] = ResourceType.MOTION
    id: UUID
    id_v1: str | None = None
    owner: OwnerReference
    motion: MotionData


class GroupedLightResource(BaseModel):
    type: Literal[ResourceType.GROUPED_LIGHT] = ResourceType.GROUPED_LIGHT
    id: UUID
    id_v1: str | None = None
    owner: OwnerReference | None = None
    on: OnState | None = None
    dimming: DimmingState | None = None


class SceneResource(BaseModel):
    type: Literal[ResourceType.SCENE] = ResourceType.SCENE
    id: UUID
    id_v1: str | None = None
    status: SceneStatus


ResourceData = Annotated[
    ButtonResource
    | RelativeRotaryResource
    | LightResource
    | MotionResource
    | GroupedLightResource
    | SceneResource,
    Field(discriminator="type"),
]


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
