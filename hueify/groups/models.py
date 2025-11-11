from uuid import UUID
from enum import StrEnum
from pydantic import BaseModel, Field, TypeAdapter


class GroupType(StrEnum):
    ROOM = "room"
    ZONE = "zone"


class ResourceReference(BaseModel):
    rid: UUID
    rtype: str


class GroupArchetype(StrEnum):
    LIVING_ROOM = "living_room"
    KITCHEN = "kitchen"
    DINING = "dining"
    BEDROOM = "bedroom"
    KIDS_BEDROOM = "kids_bedroom"
    BATHROOM = "bathroom"
    NURSERY = "nursery"
    RECREATION = "recreation"
    OFFICE = "office"
    GYM = "gym"
    HALLWAY = "hallway"
    TOILET = "toilet"
    FRONT_DOOR = "front_door"
    GARAGE = "garage"
    TERRACE = "terrace"
    GARDEN = "garden"
    DRIVEWAY = "driveway"
    CARPORT = "carport"
    HOME = "home"
    DOWNSTAIRS = "downstairs"
    UPSTAIRS = "upstairs"
    TOP_FLOOR = "top_floor"
    ATTIC = "attic"
    GUEST_ROOM = "guest_room"
    STAIRCASE = "staircase"
    LOUNGE = "lounge"
    MAN_CAVE = "man_cave"
    COMPUTER = "computer"
    STUDIO = "studio"
    MUSIC = "music"
    TV = "tv"
    READING = "reading"
    CLOSET = "closet"
    STORAGE = "storage"
    LAUNDRY_ROOM = "laundry_room"
    BALCONY = "balcony"
    PORCH = "porch"
    BARBECUE = "barbecue"
    POOL = "pool"
    OTHER = "other"


class GroupMetadata(BaseModel):
    name: str
    archetype: GroupArchetype


class GroupInfo(BaseModel):
    id: UUID
    type: GroupType
    metadata: GroupMetadata
    children: list[ResourceReference] = Field(default_factory=list)
    services: list[ResourceReference] = Field(default_factory=list)
    
    @property
    def name(self) -> str:
        return self.metadata.name
    
    @property
    def archetype(self) -> GroupArchetype:
        return self.metadata.archetype


GroupInfoListAdapter = TypeAdapter(list[GroupInfo])