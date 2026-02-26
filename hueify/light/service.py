from hueify.light.models import (
    LightInfo,
)
from hueify.shared.resource import Resource


class Light(Resource[LightInfo]):
    def _get_resource_endpoint(self) -> str:
        return "/light"
