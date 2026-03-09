import logging

from hueify.exceptions import ResourceNotFoundException
from hueify.http import HttpClient
from hueify.light.cache import LightCache
from hueify.light.service import Light
from hueify.shared.resource import ActionResult
from hueify.shared.resource.colors import Color

logger = logging.getLogger(__name__)


class LightNamespace:
    """Entry point for controlling individual lights.

    Accessible as :attr:`Hueify.lights <hueify.service.Hueify.lights>`.
    All name lookups accept the exact configured light name (case-insensitive
    matching is handled by the cache layer).

    ```python
    async with Hueify() as hue:
        await hue.lights.turn_on("Desk")
        await hue.lights.set_brightness("Desk", 60)
    ```
    """

    def __init__(self, light_cache: LightCache, http_client: HttpClient) -> None:
        self._light_cache = light_cache
        self._http_client = http_client

    @property
    def names(self) -> list[str]:
        """Names of all lights currently known to the bridge."""
        return [light.metadata.name for light in self._light_cache.get_all()]

    def from_name(self, name: str) -> Light:
        """Look up a light by name and return a :class:`~hueify.light.Light` handle.

        Args:
            name: Exact light name as configured in the Hue app.

        Raises:
            :class:`~hueify.exceptions.ResourceNotFoundException`: When no
                light with that name exists in the cache.
        """
        cached_info = self._light_cache.get_by_name(name)
        if cached_info is None:
            available = [light.metadata.name for light in self._light_cache.get_all()]
            raise ResourceNotFoundException(
                resource_type="light",
                lookup_name=name,
                suggested_names=available,
            )
        return Light(
            light_info=cached_info, client=self._http_client, cache=self._light_cache
        )

    async def turn_on(self, name: str) -> ActionResult:
        """Turn the named light on."""
        light = self.from_name(name)
        return await light.turn_on()

    async def turn_off(self, name: str) -> ActionResult:
        """Turn the named light off."""
        light = self.from_name(name)
        return await light.turn_off()

    async def set_brightness(
        self, name: str, brightness_percentage: float | int
    ) -> ActionResult:
        """Set the absolute brightness of the named light.

        Args:
            name: Light name.
            brightness_percentage: Target brightness in ``[0, 100]``.
        """
        light = self.from_name(name)
        return await light.set_brightness(brightness_percentage)

    async def increase_brightness(
        self, name: str, brightness_percentage: float | int
    ) -> ActionResult:
        """Increase the brightness of the named light by a relative amount.

        Args:
            name: Light name.
            brightness_percentage: Percentage points to add.
        """
        light = self.from_name(name)
        return await light.increase_brightness(brightness_percentage)

    async def decrease_brightness(
        self, name: str, brightness_percentage: float | int
    ) -> ActionResult:
        """Decrease the brightness of the named light by a relative amount.

        Args:
            name: Light name.
            brightness_percentage: Percentage points to subtract.
        """
        light = self.from_name(name)
        return await light.decrease_brightness(brightness_percentage)

    async def set_color_temperature(
        self, name: str, color_temperature_percentage: float | int
    ) -> ActionResult:
        """Set the colour temperature of the named light.

        Args:
            name: Light name.
            color_temperature_percentage: ``0`` = warmest white, ``100`` = coolest.
        """
        light = self.from_name(name)
        return await light.set_color_temperature(color_temperature_percentage)

    async def set_color(self, name: str, r: int, g: int, b: int) -> ActionResult:
        """Set the colour of the named light using sRGB values.

        Args:
            name: Light name.
            r: Red channel in ``[0, 255]``.
            g: Green channel in ``[0, 255]``.
            b: Blue channel in ``[0, 255]``.
        """
        light = self.from_name(name)
        return await light.set_color(r, g, b)

    async def set_named_color(self, name: str, color: Color) -> ActionResult:
        """Set the colour of the named light to a predefined :class:`~hueify.shared.resource.Color`.

        Args:
            name: Light name.
            color: Named colour constant, e.g. ``Color.WARM_WHITE``.
        """
        light = self.from_name(name)
        return await light.set_named_color(color)

    def get_brightness(self, name: str) -> float:
        """Return the current brightness of the named light as a percentage."""
        light = self.from_name(name)
        return light.brightness_percentage
