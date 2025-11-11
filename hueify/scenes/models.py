from enum import StrEnum
from uuid import UUID
from pydantic import BaseModel, Field, TypeAdapter


class SceneStatusValue(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    STATIC = "static"


class SceneStatus(BaseModel):
    active: SceneStatusValue


class SceneAction(StrEnum):
    ACTIVE = "active"
    DYNAMIC_PALETTE = "dynamic_palette"
    STATIC = "static"


class ResourceReference(BaseModel):
    rid: UUID
    rtype: str


class SceneMetadata(BaseModel):
    name: str
    image: ResourceReference | None = None


class SceneGroup(BaseModel):
    rid: UUID
    rtype: str = "room"


class SceneActionTarget(BaseModel):
    target: ResourceReference
    action: dict


class ScenePalette(BaseModel):
    color: list[dict] = Field(default_factory=list)
    dimming: list[dict] = Field(default_factory=list)
    color_temperature: list[dict] = Field(default_factory=list)
    effects: list[dict] = Field(default_factory=list)
    effects_v2: list[dict] = Field(default_factory=list)


class SceneInfo(BaseModel):
    id: UUID
    metadata: SceneMetadata
    group: SceneGroup
    actions: list[SceneActionTarget] = Field(default_factory=list)
    palette: ScenePalette = Field(default_factory=ScenePalette)
    speed: float = 0.5
    auto_dynamic: bool = False
    status: SceneStatus | None = None
    type: str = "scene"
    
    @property
    def name(self) -> str:
        return self.metadata.name
    
    @property
    def group_id(self) -> UUID:
        return self.group.rid

    class Config:
        populate_by_name = True


SceneInfoListAdapter = TypeAdapter(list[SceneInfo])


class SceneRecall(BaseModel):
    action: SceneAction = SceneAction.ACTIVE
    duration: int | None = None
    dimming: dict | None = None


class SceneActivationRequest(BaseModel):
    recall: SceneRecall


class SceneActivationResponse(BaseModel):
    errors: list[dict] = Field(default_factory=list)
    data: list[dict] = Field(default_factory=list)