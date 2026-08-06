from collections.abc import Callable
from types import TracebackType
from typing import Self, overload

from hueify.credentials import load_credentials
from hueify.http import HttpClient
from hueify.models import HueEvent
from hueify.resources import (
    LightNamespace,
    RoomNamespace,
    SceneNamespace,
    ZoneNamespace,
)
from hueify.sse import (
    EventHandler,
    EventResourceType,
    EventStream,
    ReconnectPolicy,
)


class Hueify:
    """Typed, stateless client for the Philips Hue CLIP v2 API.

    Credentials are read from the constructor arguments, the
    ``HUE_BRIDGE_IP``/``HUE_APP_KEY`` environment variables and a ``.env``
    file, in that order.
    """

    def __init__(
        self,
        bridge_ip: str | None = None,
        app_key: str | None = None,
        reconnect: ReconnectPolicy | None = None,
    ) -> None:
        self._credentials = load_credentials(bridge_ip, app_key)
        self._http_client = HttpClient(self._credentials)
        self.lights = LightNamespace(self._http_client)
        self.rooms = RoomNamespace(self._http_client)
        self.zones = ZoneNamespace(self._http_client)
        self.scenes = SceneNamespace(self._http_client)
        self.events = EventStream(self._credentials, reconnect)

    async def __aenter__(self) -> Self:
        return self

    @overload
    def on[T: HueEvent](
        self, resource_type: EventResourceType, handler: EventHandler[T]
    ) -> EventHandler[T]: ...

    @overload
    def on[T: HueEvent](
        self, resource_type: EventResourceType, handler: None = None
    ) -> Callable[[EventHandler[T]], EventHandler[T]]: ...

    def on[T: HueEvent](
        self,
        resource_type: EventResourceType,
        handler: EventHandler[T] | None = None,
    ) -> EventHandler[T] | Callable[[EventHandler[T]], EventHandler[T]]:
        """Shortcut for ``hue.events.on`` - registering handlers reads better here."""
        return self.events.on(resource_type, handler)

    def off[T: HueEvent](
        self, resource_type: EventResourceType, handler: EventHandler[T]
    ) -> None:
        self.events.off(resource_type, handler)

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.close()

    async def close(self) -> None:
        await self.events.stop()
        await self._http_client.close()
