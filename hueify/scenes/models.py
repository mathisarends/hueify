from enum import StrEnum
from pydantic import BaseModel

class LightSceneType(StrEnum):
    LIGHTSCENE = "LightScene"
    GROUPSCENE = "GroupScene"


class SceneInfo(BaseModel):
    id: str
    name: str
    group_id: str
    type: LightSceneType
    lights: list[str]
    owner: str
    recycle: bool = False
    locked: bool = False
    picture: str
    image: str
    lastupdated: str
    version: int = 0