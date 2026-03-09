from hueify.light.views import (
    LightInfo,
)
from hueify.shared.resource import Resource


class Light(Resource[LightInfo]):
    """Represents a single Philips Hue light.

    Inherits all control methods from :class:`~hueify.shared.resource.Resource`:
    :meth:`~hueify.shared.resource.Resource.turn_on`,
    :meth:`~hueify.shared.resource.Resource.turn_off`,
    :meth:`~hueify.shared.resource.Resource.set_brightness`,
    :meth:`~hueify.shared.resource.Resource.increase_brightness`,
    :meth:`~hueify.shared.resource.Resource.decrease_brightness`, and
    :meth:`~hueify.shared.resource.Resource.set_color_temperature`.

    Obtain an instance via :attr:`Hueify.lights` rather than constructing
    directly:

    ```python
    light = hue.lights.from_name("Desk")
    await light.turn_on()
    ```
    """

    def _get_resource_endpoint(self) -> str:
        return "/light"
