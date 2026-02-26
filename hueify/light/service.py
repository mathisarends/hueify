from pydantic import BaseModel

from hueify.light.models import (
    LightInfo,
)
from hueify.shared.resource import Resource


class Light(Resource[LightInfo]):
    @property
    def name(self) -> str:
        return self._light_info.metadata.name

    def _get_resource_endpoint(self) -> str:
        return "light"

    async def _update_remote_state(self, state: BaseModel) -> None:
        endpoint = self._get_resource_endpoint()
        await self._client.put(f"{endpoint}/{self.id}", data=state)
