from hueify.light.views import (
    LightInfo,
)
from hueify.shared.resource import Resource


class Light(Resource[LightInfo]):
    @property
    def name(self) -> str:
        return self._light_info.metadata.name

    def _get_resource_endpoint(self) -> str:
        return "/light"
