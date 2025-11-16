from enum import StrEnum
from typing import Annotated, Any, Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from hueify.shared.types.resource import ResourceType


class EventType(StrEnum):
    UPDATE = "update"
    ADD = "add"
    DELETE = "delete"


class ButtonEvent(StrEnum):
    INITIAL_PRESS = "initial_press"
    REPEAT = "repeat"
    SHORT_RELEASE = "short_release"
    LONG_PRESS = "long_press"
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


class ButtonEvent(BaseModel):
    type: Literal[ResourceType.BUTTON] = ResourceType.BUTTON
    id: UUID
    id_v1: str | None = None
    owner: OwnerReference
    button: ButtonData


class RelativeRotaryEvent(BaseModel):
    type: Literal[ResourceType.RELATIVE_ROTARY] = ResourceType.RELATIVE_ROTARY
    id: UUID
    id_v1: str | None = None
    owner: OwnerReference
    relative_rotary: RelativeRotaryData


class LightEvent(BaseModel):
    type: Literal[ResourceType.LIGHT] = ResourceType.LIGHT
    id: UUID
    id_v1: str | None = None
    owner: OwnerReference
    service_id: int | None = None
    on: OnState | None = None
    dimming: DimmingState | None = None
    color: ColorState | None = None
    color_temperature: ColorTemperature | None = None


class MotionEvent(BaseModel):
    type: Literal[ResourceType.MOTION] = ResourceType.MOTION
    id: UUID
    id_v1: str | None = None
    owner: OwnerReference
    motion: MotionData


class GroupedLightEvent(BaseModel):
    type: Literal[ResourceType.GROUPED_LIGHT] = ResourceType.GROUPED_LIGHT
    id: UUID
    id_v1: str | None = None
    owner: OwnerReference | None = None
    on: OnState | None = None
    dimming: DimmingState | None = None


class SceneEvent(BaseModel):
    type: Literal[ResourceType.SCENE] = ResourceType.SCENE
    id: UUID
    id_v1: str | None = None
    status: SceneStatus


HueEvent = Annotated[
    ButtonEvent
    | RelativeRotaryEvent
    | LightEvent
    | MotionEvent
    | GroupedLightEvent
    | SceneEvent,
    Field(discriminator="type"),
]


class UnknownEvent(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: UUID
    type: str
    id_v1: str | None = None
    owner: OwnerReference | None = None
    service_id: int | None = None

    @property
    def extra_fields(self) -> dict[str, Any]:
        return {
            k: v
            for k, v in self.__dict__.items()
            if k not in self.__class__.model_fields
        }


class EventData(BaseModel):
    creationtime: str
    data: list[HueEvent | UnknownEvent]
    id: UUID
    type: EventType


class Event(BaseModel):
    events: list[EventData]

    @classmethod
    def from_sse_data(cls, sse_data_list: list[dict]) -> Self:
        return cls(events=sse_data_list)
