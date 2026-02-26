import asyncio
from types import TracebackType
from typing import Self

from hueify.cache import LookupCache
from hueify.credentials import HueBridgeCredentials
from hueify.http import HttpClient
from hueify.namespaces import LightNamespace, RoomNamespace, ZoneNamespace
from hueify.sse import EventBus, ServerSentEventStream


class Hueify:
    def __init__(
        self,
        bridge_ip: str | None = None,
        app_key: str | None = None,
    ) -> None:
        credentials = self._resolve_credentials(bridge_ip, app_key)

        self._credentials = credentials
        self._http_client = HttpClient(self._credentials)
        self._event_bus = EventBus()
        self._event_stream = ServerSentEventStream(
            credentials=self._credentials, event_bus=self._event_bus
        )
        self._cache = LookupCache(self._event_bus)
        self._stream_task: asyncio.Task | None = None

        self.lights = LightNamespace(self._cache)
        self.rooms = RoomNamespace(self._cache)
        self.zones = ZoneNamespace(self._cache)

    def _resolve_credentials(
        self,
        bridge_ip: str | None,
        app_key: str | None,
    ) -> HueBridgeCredentials:
        if bridge_ip is not None and app_key is not None:
            return HueBridgeCredentials(hue_bridge_ip=bridge_ip, hue_app_key=app_key)
        return HueBridgeCredentials()

    async def __aenter__(self) -> Self:
        self._stream_task = asyncio.create_task(self._event_stream.connect())
        await self._cache.populate()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self._event_stream.disconnect()
        if self._stream_task and not self._stream_task.done():
            self._stream_task.cancel()
        await self._http_client.close()
        await self._cache.clear_all()
