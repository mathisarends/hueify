from hueify.groups.base import GroupLookup
from hueify.groups.rooms.exceptions import RoomNotFoundException


class RoomLookup(GroupLookup):
    def _get_endpoint(self) -> str:
        return "room"

    def _create_not_found_exception(
        self, 
        lookup_name: str, 
        suggested_names: list[str]
    ) -> Exception:
        return RoomNotFoundException(
            lookup_name=lookup_name,
            suggested_names=suggested_names
        )