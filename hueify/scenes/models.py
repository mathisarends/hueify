from enum import StrEnum
from typing import Literal, Self
from uuid import UUID

from pydantic import BaseModel, Field, TypeAdapter

from hueify.shared.types.resource import ResourceReference, ResourceType


class SceneStatusValue(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    STATIC = "static"
    DYNAMIC_PALETTE = "dynamic_palette"


class SceneStatus(BaseModel):
    active: SceneStatusValue


class SceneAction(StrEnum):
    ACTIVE = "active"
    DYNAMIC_PALETTE = "dynamic_palette"
    STATIC = "static"


class ImageResourceReference(BaseModel):
    rid: UUID
    rtype: Literal[ResourceType.PUBLIC_IMAGE] = ResourceType.PUBLIC_IMAGE


class SceneMetadata(BaseModel):
    name: str
    image: ImageResourceReference | None = None


class SceneActionTarget(BaseModel):
    target: ResourceReference
    action: dict


# Diese Modelle hier müssen viel besser getyped werden
class ScenePalette(BaseModel):
    color: list[dict] = Field(default_factory=list)
    dimming: list[dict] = Field(default_factory=list)
    color_temperature: list[dict] = Field(default_factory=list)
    effects: list[dict] = Field(default_factory=list)
    effects_v2: list[dict] = Field(default_factory=list)


class SceneInfo(BaseModel):
    id: UUID
    metadata: SceneMetadata
    group: ResourceReference
    actions: list[SceneActionTarget] = Field(default_factory=list)
    palette: ScenePalette = Field(default_factory=ScenePalette)
    speed: float = 0.5
    auto_dynamic: bool = False
    status: SceneStatus | None = None
    type: Literal[ResourceType.SCENE] = ResourceType.SCENE

    @property
    def name(self) -> str:
        return self.metadata.name

    @property
    def group_id(self) -> UUID:
        return self.group.rid


class ShortSceneInfo(BaseModel):
    id: UUID
    name: str
    group_id: UUID

    @classmethod
    def from_scene_info(cls, scene_info: SceneInfo) -> Self:
        return cls(
            id=scene_info.id,
            name=scene_info.metadata.name,
            group_id=scene_info.group.rid,
        )


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
