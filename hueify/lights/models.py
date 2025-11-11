from uuid import UUID
from pydantic import BaseModel, Field, TypeAdapter


class LightState(BaseModel):
    on: bool


class LightStateUpdate(BaseModel):
    on: bool = Field(..., description="Turn light on or off")


class LightInfo(BaseModel):
    id: UUID
    type: str
    owner: dict | None = None
    metadata: dict | None = None
    on: dict | None = None
    dimming: dict | None = None
    color_temperature: dict | None = None


LightInfoListAdapter = TypeAdapter(list[LightInfo])
