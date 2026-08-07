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
        return await self.update(
            area_id, EntertainmentConfigurationUpdate(action=StreamAction.START)
        )

    async def stop(self, area_id: ResourceId) -> HueApiResponse[ResourceIdentifier]:
        return await self.update(
            area_id, EntertainmentConfigurationUpdate(action=StreamAction.STOP)
        )

    async def is_streaming(self, area_id: ResourceId) -> bool:
        return (await self.get_one(area_id)).is_streaming

    def stream(
        self,
        area: EntertainmentConfiguration | ResourceId,
        rate: int = DEFAULT_RATE,
    ) -> EntertainmentStream:
        return EntertainmentStream(area, self, self._credentials, rate)
