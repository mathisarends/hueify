from enum import StrEnum
from pydantic import BaseModel, Field, TypeAdapter


class LightSceneType(StrEnum):
    LIGHTSCENE = "LightScene"
    GROUPSCENE = "GroupScene"


class SceneInfo(BaseModel):
    id: str
    name: str
    group_id: str = Field(alias="group")
    type: LightSceneType
    lights: list[str]

    class Config:
        populate_by_name = True

SceneInfoListAdapter = TypeAdapter(list[SceneInfo])

class SceneActivationRequest(BaseModel):
    scene: str


class SceneActivationResponse(BaseModel):
    success: dict[str, str]


class ScenesResponse(BaseModel):
    scenes: dict[str, SceneInfo] = Field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, dict]) -> "ScenesResponse":
        scenes = {}
        for scene_id, scene_data in data.items():
            scene_data["id"] = scene_id
            scenes[scene_id] = SceneInfo.model_validate(scene_data)
        return cls(scenes=scenes)