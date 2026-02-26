from enum import StrEnum
from typing import Literal, Self
from uuid import UUID

from pydantic import BaseModel, Field, TypeAdapter

from hueify.shared.resource.models import ResourceReference, ResourceType


class SceneStatusValue(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    STATIC = "static"
    DYNAMIC_PALETTE = "dynamic_palette"


class SceneStatus(BaseModel):
    active: SceneStatusValue | None = None
    last_recall: str | None = None


class SceneAction(StrEnum):
    ACTIVE = "active"
    DYNAMIC_PALETTE = "dynamic_palette"
    STATIC = "static"


class EffectType(StrEnum):
    PRISM = "prism"
    OPAL = "opal"
    GLISTEN = "glisten"
    SPARKLE = "sparkle"
    FIRE = "fire"
    CANDLE = "candle"
    UNDERWATER = "underwater"
    COSMOS = "cosmos"
    SUNBEAM = "sunbeam"
    ENCHANT = "enchant"
    NO_EFFECT = "no_effect"


class ColorXY(BaseModel):
    x: float = Field(ge=0, le=1)
    y: float = Field(ge=0, le=1)


class ColorPaletteEntry(BaseModel):
    color: dict | None = None


class DimmingPaletteEntry(BaseModel):
    dimming: dict | None = None


class ColorTemperaturePaletteEntry(BaseModel):
    color_temperature: dict | None = None


class SceneActionTarget(BaseModel):
    target: ResourceReference
    action: dict = Field(default_factory=dict)


class ImageResourceReference(BaseModel):
    rid: UUID
    rtype: Literal[ResourceType.PUBLIC_IMAGE] = ResourceType.PUBLIC_IMAGE


class SceneMetadata(BaseModel):
    name: str = Field(min_length=1, max_length=32)
    image: ImageResourceReference | None = None
    appdata: str | None = Field(default=None, min_length=1, max_length=16)


class ScenePalette(BaseModel):
    color: list[dict] = Field(default_factory=list)
    dimming: list[dict] = Field(default_factory=list)
    color_temperature: list[dict] = Field(default_factory=list)
    effects: list[dict] = Field(default_factory=list)
    effects_v2: list[dict] = Field(default_factory=list)


class SceneInfo(BaseModel):
    id: UUID
    type: Literal[ResourceType.SCENE] = ResourceType.SCENE
    metadata: SceneMetadata
    group: ResourceReference
    actions: list[SceneActionTarget] = Field(default_factory=list)
    palette: ScenePalette = Field(default_factory=ScenePalette)
    speed: float = Field(default=0.5, ge=0, le=1)
    auto_dynamic: bool = False
    status: SceneStatus | None = None
    id_v1: str | None = None

    @property
    def name(self) -> str:
        return self.metadata.name

    @property
    def group_id(self) -> UUID:
        return self.group.rid

    @property
    def is_active(self) -> bool:
        return (
            self.status is not None and self.status.active != SceneStatusValue.INACTIVE
        )


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
