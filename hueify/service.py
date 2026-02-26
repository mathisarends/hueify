import asyncio
import logging
from types import TracebackType
from typing import Self

from hueify.cache import ManagedCache
from hueify.credentials import HueBridgeCredentials
from hueify.grouped_lights import (
    GroupedLightCache,
    RoomCache,
    RoomNamespace,
    ZoneCache,
    ZoneNamespace,
)
from hueify.http import HttpClient
from hueify.light import LightCache, LightNamespace
from hueify.scenes import SceneCache
from hueify.shared.decorators import timed
from hueify.sse import EventBus, ServerSentEventStream

logger = logging.getLogger(__name__)


class Hueify:
    def __init__(
        self,
        bridge_ip: str | None = None,
        app_key: str | None = None,
    ) -> None:
        logger.debug(f"Initializing Hueify with bridge_ip={bridge_ip}")
        self._credentials = self._resolve_credentials(bridge_ip, app_key)

        self._http_client = HttpClient(self._credentials)
        self._event_bus = EventBus()
        self._event_stream = ServerSentEventStream(
            credentials=self._credentials, event_bus=self._event_bus
        )
        self._stream_task: asyncio.Task | None = None

        self._light_cache = LightCache(self._event_bus)
        self._grouped_light_cache = GroupedLightCache(self._event_bus)
        self._room_cache = RoomCache()
        self._zone_cache = ZoneCache()
        self._scene_cache = SceneCache(self._event_bus)

        self._caches: list[ManagedCache] = [
            self._light_cache,
            self._grouped_light_cache,
            self._room_cache,
            self._zone_cache,
            self._scene_cache,
        ]

        self.lights = LightNamespace(self._light_cache, self._http_client)
        self.rooms = RoomNamespace(
            room_cache=self._room_cache,
            grouped_light_cache=self._grouped_light_cache,
            http_client=self._http_client,
            scene_cache=self._scene_cache,
        )
        self.zones = ZoneNamespace(
            zone_cache=self._zone_cache,
            grouped_light_cache=self._grouped_light_cache,
            http_client=self._http_client,
            scene_cache=self._scene_cache,
        )
        logger.info("Hueify initialized successfully")

    def _resolve_credentials(
        self,
        bridge_ip: str | None,
        app_key: str | None,
    ) -> HueBridgeCredentials:
        if bridge_ip is not None and app_key is not None:
            return HueBridgeCredentials(hue_bridge_ip=bridge_ip, hue_app_key=app_key)
        return HueBridgeCredentials()

    async def __aenter__(self) -> Self:
        await self.connect()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.close()

    @timed()
    async def connect(self) -> None:
        logger.info("Connecting to Hue Bridge")
        self._stream_task = asyncio.create_task(self._event_stream.connect())
        logger.debug("Event stream connection task created")

        await self._populate_caches()
        logger.info("Caches populated successfully")

    async def _populate_caches(self) -> None:
        await asyncio.gather(*[c.populate(self._http_client) for c in self._caches])
        logger.info("Caches populated successfully")

    async def close(self) -> None:
        logger.info("Disconnecting from Hue Bridge")
        self._event_stream.disconnect()
        logger.debug("Event stream disconnected")

        if self._stream_task and not self._stream_task.done():
            self._stream_task.cancel()
            logger.debug("Event stream task cancelled")

        await self._http_client.close()
        self._clear_caches()

    def _clear_caches(self) -> None:
        for c in self._caches:
            c.clear()
        logger.info("All caches cleared")
