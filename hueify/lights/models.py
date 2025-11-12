from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, TypeAdapter


class OnState(BaseModel):
    on: bool


class DimmingState(BaseModel):
    brightness: float = Field(ge=0, le=100)


class ColorTemperatureState(BaseModel):
    mirek: int | None = Field(default=None, ge=153, le=500)


class ColorXY(BaseModel):
    x: float = Field(ge=0, le=1)
    y: float = Field(ge=0, le=1)


class ColorState(BaseModel):
    xy: ColorXY


class ResourceReference(BaseModel):
    rid: UUID
    rtype: str


class LightMetadata(BaseModel):
    name: str
    archetype: str | None = None


class LightState(BaseModel):
    on: OnState | None = None
    dimming: DimmingState | None = None
    color_temperature: ColorTemperatureState | None = None
    color: ColorState | None = None


class LightInfo(BaseModel):
    id: UUID
    type: str
    owner: ResourceReference
    metadata: LightMetadata
    on: dict[str, Any] | None = None
    dimming: dict[str, Any] | None = None
    color_temperature: dict[str, Any] | None = None
    color: dict[str, Any] | None = None


LightInfoListAdapter = TypeAdapter(list[LightInfo])
