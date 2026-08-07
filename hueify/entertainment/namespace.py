"""The ``entertainment_configuration`` endpoint, and where a stream starts.

Areas are created in the Hue app - they carry the room geometry a user placed
their lamps in, which is not something a library should invent. What this
namespace does is find them, hand out their channels, and hand over control:
``start`` puts an area into streaming mode, after which the bridge stops taking
REST commands for those lamps and listens on UDP instead.
"""

from pydantic import TypeAdapter

from hueify.credentials import HueBridgeCredentials
from hueify.entertainment.stream import DEFAULT_RATE, EntertainmentStream
from hueify.http import HttpClient
from hueify.models import (
    EntertainmentConfiguration,
    EntertainmentConfigurationUpdate,
    HueApiResponse,
    ResourceIdentifier,
    StreamAction,
)
from hueify.resources.base import ResourceId, ResourceNamespace

ENTERTAINMENT_CONFIGURATION_RESOURCE_TYPE = "entertainment_configuration"


class EntertainmentNamespace(ResourceNamespace[EntertainmentConfiguration]):
    """The entertainment areas of the bridge, and the streams to them."""

    def __init__(
        self, http_client: HttpClient, credentials: HueBridgeCredentials
    ) -> None:
        super().__init__(
            ENTERTAINMENT_CONFIGURATION_RESOURCE_TYPE,
            TypeAdapter(HueApiResponse[EntertainmentConfiguration]),
            http_client,
        )
        self._credentials = credentials

    async def update(
        self, area_id: ResourceId, data: EntertainmentConfigurationUpdate
    ) -> HueApiResponse[ResourceIdentifier]:
        return await self._update(area_id, data)

    async def start(self, area_id: ResourceId) -> HueApiResponse[ResourceIdentifier]:
        """Put the area into streaming mode, so the bridge expects datagrams.

        The bridge drops the area again on its own when nothing arrives for a
        few seconds, and refuses this call while another application streams
        to it.
        """
        return await self.update(
            area_id, EntertainmentConfigurationUpdate(action=StreamAction.START)
        )

    async def stop(self, area_id: ResourceId) -> HueApiResponse[ResourceIdentifier]:
        """Leave streaming mode and give the lamps back to the REST API."""
        return await self.update(
            area_id, EntertainmentConfigurationUpdate(action=StreamAction.STOP)
        )

    async def is_streaming(self, area_id: ResourceId) -> bool:
        """Whether some application is currently streaming to the area."""
        return (await self.get_one(area_id)).is_streaming

    def stream(
        self,
        area: EntertainmentConfiguration | ResourceId,
        rate: int = DEFAULT_RATE,
    ) -> EntertainmentStream:
        """A streaming session for one area, not started yet.

        Nothing happens until it is opened, which is what makes it usable as an
        async context manager::

            async with hue.entertainment.stream(area) as stream:
                stream.set_all("#ff8800")

        Args:
            area: An area, or the ID of one to read on open.
            rate: Frames per second, up to 60.

        Raises:
            MissingCredentialsError: If no client key is configured.
            ValueError: If the rate is out of range.
        """
        return EntertainmentStream(area, self, self._credentials, rate)
