from functools import cached_property

from pydantic import BaseModel

from hueify.grouped_lights.models import GroupedLightInfo
from hueify.shared.resource import Resource


class GroupedLights(Resource[GroupedLightInfo]):
    @cached_property
    def name(self) -> str:
        return self._light_info.name

    def _get_resource_endpoint(self) -> str:
        return "grouped_light"

    async def _update_remote_state(self, state: BaseModel) -> None:
        endpoint = self._get_resource_endpoint()
        await self._client.put(f"{endpoint}/{self.id}", data=state)
