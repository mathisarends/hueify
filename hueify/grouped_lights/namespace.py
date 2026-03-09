import logging

from hueify.cache.lookup import NamedEntityLookupCache
from hueify.exceptions import ResourceNotFoundException
from hueify.grouped_lights.cache import GroupedLightCache
from hueify.grouped_lights.service import GroupedLights
from hueify.grouped_lights.views import GroupInfo
from hueify.http import HttpClient
from hueify.scenes.cache import SceneCache
from hueify.shared.resource import ActionResult
from hueify.shared.resource.colors import Color

logger = logging.getLogger(__name__)


class GroupNamespace:
    """Base namespace for room- and zone-level grouped-light control.

    Subclassed by :class:`~hueify.grouped_lights.RoomNamespace` and
    :class:`~hueify.grouped_lights.ZoneNamespace`, which are exposed as
    :attr:`Hueify.rooms <hueify.service.Hueify.rooms>` and
    :attr:`Hueify.zones <hueify.service.Hueify.zones>` respectively.
    """

    def __init__(
        self,
        group_cache: NamedEntityLookupCache[GroupInfo],
        resource_type: str,
        grouped_light_cache: GroupedLightCache,
        http_client: HttpClient,
        scene_cache: SceneCache,
    ) -> None:
        self._group_cache = group_cache
        self._resource_type = resource_type
        self._grouped_light_cache = grouped_light_cache
        self._http_client = http_client
        self._scene_cache = scene_cache

    @property
    def names(self) -> list[str]:
        """Names of all groups currently known to the bridge."""
        return [g.metadata.name for g in self._group_cache.get_all()]

    def from_name(self, name: str) -> GroupedLights:
        """Look up a group by name and return a :class:`~hueify.grouped_lights.GroupedLights` handle.

        Args:
            name: Exact group name as configured in the Hue app.

        Raises:
            :class:`~hueify.exceptions.ResourceNotFoundException`: When no
                matching group is found.
        """
        group_info = self._group_cache.get_by_name(name)
        if group_info is None:
            available = [g.metadata.name for g in self._group_cache.get_all()]
            raise ResourceNotFoundException(
                resource_type=self._resource_type,
                lookup_name=name,
                suggested_names=available,
            )

        grouped_light_id = group_info.get_grouped_light_reference_if_exists()
        if grouped_light_id is None:
            raise ValueError(f"Group '{name}' has no grouped_light service reference")

        grouped_light_info = self._grouped_light_cache.get_by_id(grouped_light_id)
        if grouped_light_info is None:
            raise ValueError(
                f"GroupedLight {grouped_light_id} not in cache for group '{name}'"
            )

        return GroupedLights(
            light_info=grouped_light_info,
            client=self._http_client,
            group_info=group_info,
            scene_cache=self._scene_cache,
            cache=self._grouped_light_cache,
        )

    async def turn_on(self, name: str) -> ActionResult:
        """Turn all lights in the named group on."""
        group = self.from_name(name)
        return await group.turn_on()

    async def turn_off(self, name: str) -> ActionResult:
        """Turn all lights in the named group off."""
        group = self.from_name(name)
        return await group.turn_off()

    async def set_brightness(self, name: str, percentage: float | int) -> ActionResult:
        """Set the absolute brightness for all lights in the named group.

        Args:
            name: Group name.
            percentage: Target brightness in ``[0, 100]``.
        """
        group = self.from_name(name)
        return await group.set_brightness(percentage)

    async def increase_brightness(
        self, name: str, percentage: float | int
    ) -> ActionResult:
        """Increase brightness of the named group by a relative amount.

        Args:
            name: Group name.
            percentage: Percentage points to add.
        """
        group = self.from_name(name)
        return await group.increase_brightness(percentage)

    async def decrease_brightness(
        self, name: str, percentage: float | int
    ) -> ActionResult:
        """Decrease brightness of the named group by a relative amount.

        Args:
            name: Group name.
            percentage: Percentage points to subtract.
        """
        group = self.from_name(name)
        return await group.decrease_brightness(percentage)

    async def set_color_temperature(
        self, name: str, percentage: float | int
    ) -> ActionResult:
        """Set the colour temperature for all lights in the named group.

        Args:
            name: Group name.
            percentage: ``0`` = warmest white, ``100`` = coolest.
        """
        group = self.from_name(name)
        return await group.set_color_temperature(percentage)

    async def set_color(self, name: str, r: int, g: int, b: int) -> ActionResult:
        """Set the colour of all lights in the named group using sRGB values.

        Args:
            name: Group name.
            r: Red channel in ``[0, 255]``.
            g: Green channel in ``[0, 255]``.
            b: Blue channel in ``[0, 255]``.
        """
        group = self.from_name(name)
        return await group.set_color(r, g, b)

    async def set_named_color(self, name: str, color: Color) -> ActionResult:
        """Set the colour of all lights in the named group to a predefined :class:`~hueify.shared.resource.Color`.

        Args:
            name: Group name.
            color: Named colour constant, e.g. ``Color.WARM_WHITE``.
        """
        group = self.from_name(name)
        return await group.set_named_color(color)

    def get_brightness(self, name: str) -> float:
        """Return the current brightness of the named group as a percentage."""
        group = self.from_name(name)
        return group.brightness_percentage

    def scene_names(self, name: str) -> list[str]:
        """Return the names of all scenes available for the named group."""
        group = self.from_name(name)
        return group.scene_names

    async def activate_scene(self, name: str, scene_name: str) -> ActionResult:
        """Activate a scene for the named group.

        Args:
            name: Group name.
            scene_name: Scene name (case-insensitive).

        Raises:
            :class:`~hueify.exceptions.ResourceNotFoundException`: When the
                scene is not found for this group.
        """
        group = self.from_name(name)
        return await group.activate_scene(scene_name)
