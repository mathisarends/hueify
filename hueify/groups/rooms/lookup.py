from hueify.groups.models import GroupInfo
from hueify.groups.rooms.exceptions import RoomNotFoundException
from hueify.shared.resource.lookup import NamedResourceLookup
from hueify.shared.resource.models import ResourceType


class RoomLookup(NamedResourceLookup[GroupInfo]):
    def get_resource_type(self) -> ResourceType:
        return ResourceType.ROOM

    def get_model_type(self) -> type[GroupInfo]:
        return GroupInfo

    def _get_endpoint(self) -> str:
        return "room"

    def _create_not_found_exception(
        self, lookup_name: str, suggested_names: list[str]
    ) -> Exception:
        return RoomNotFoundException(
            lookup_name=lookup_name, suggested_names=suggested_names
        )
