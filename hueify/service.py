import asyncio
import logging
from types import TracebackType
from typing import Self

from hueify.credentials import HueBridgeCredentials
from hueify.grouped_lights.cache import GroupedLightCache
from hueify.grouped_lights.models import GroupedLightInfo
from hueify.groups.models import GroupInfo
from hueify.http import HttpClient
from hueify.light import LightCache, LightNamespace
from hueify.light.models import LightInfo
from hueify.room import RoomCache, RoomNamespace
from hueify.scenes import SceneCache
from hueify.scenes.models import SceneInfo
from hueify.sse import EventBus, ServerSentEventStream
from hueify.zone import ZoneCache, ZoneNamespace

logger = logging.getLogger(__name__)


class Hueify:
    def __init__(
        self,
        bridge_ip: str | None = None,
        app_key: str | None = None,
    ) -> None:
        logger.debug(f"Initializing Hueify with bridge_ip={bridge_ip}")
        credentials = self._resolve_credentials(bridge_ip, app_key)

        self._credentials = credentials
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

        self.lights = LightNamespace(self._light_cache, self._http_client)
        self.rooms = RoomNamespace(
            self._room_cache,
            self._grouped_light_cache,
            self._http_client,
            self._scene_cache,
        )
        self.zones = ZoneNamespace(
            self._zone_cache,
            self._grouped_light_cache,
            self._http_client,
            self._scene_cache,
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
        logger.info("Connecting to Hue Bridge")
        self._stream_task = asyncio.create_task(self._event_stream.connect())
        logger.debug("Event stream connection task created")

        await self._populate_caches()
        logger.info("Caches populated successfully")
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        logger.info("Disconnecting from Hue Bridge")
        self._event_stream.disconnect()
        logger.debug("Event stream disconnected")

        if self._stream_task and not self._stream_task.done():
            self._stream_task.cancel()
            logger.debug("Event stream task cancelled")

        await self._http_client.close()
        await self._clear_caches()

    async def _populate_caches(self) -> None:
        lights, rooms, zones, scenes, grouped_lights = await asyncio.gather(
            self._http_client.get_resources(endpoint="/light", resource_type=LightInfo),
            self._http_client.get_resources(endpoint="/room", resource_type=GroupInfo),
            self._http_client.get_resources(endpoint="/zone", resource_type=GroupInfo),
            self._http_client.get_resources(endpoint="/scene", resource_type=SceneInfo),
            self._http_client.get_resources(
                endpoint="/grouped_light", resource_type=GroupedLightInfo
            ),
        )
        await asyncio.gather(
            self._light_cache.store_all(lights),
            self._room_cache.store_all(rooms),
            self._zone_cache.store_all(zones),
            self._scene_cache.store_all(scenes),
            self._grouped_light_cache.store_all(grouped_lights),
        )
        logger.info(
            f"Caches populated — lights={len(lights)}, rooms={len(rooms)}, "
            f"zones={len(zones)}, scenes={len(scenes)}, "
            f"grouped_lights={len(grouped_lights)}"
        )

    async def _clear_caches(self) -> None:
        await asyncio.gather(
            self._light_cache.clear(),
            self._room_cache.clear(),
            self._zone_cache.clear(),
            self._scene_cache.clear(),
            self._grouped_light_cache.clear(),
        )
        logger.info("All caches cleared")
