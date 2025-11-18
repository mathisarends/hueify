from typing import override

from hueify.groups.models import GroupInfo
from hueify.groups.rooms.exceptions import RoomNotFoundException
from hueify.shared.resource.lookup import NamedResourceLookup
from hueify.shared.resource.models import ResourceType


class RoomLookup(NamedResourceLookup[GroupInfo]):
    @override
    def get_resource_type(self) -> ResourceType:
        return ResourceType.ROOM

    @override
    def get_model_type(self) -> type[GroupInfo]:
        return GroupInfo

    @override
    def _get_endpoint(self) -> str:
        return "room"

    @override
    def _create_not_found_exception(
        self, lookup_name: str, suggested_names: list[str]
    ) -> Exception:
        return RoomNotFoundException(
            lookup_name=lookup_name, suggested_names=suggested_names
        )
