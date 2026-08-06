import logging

import httpx
from httpx_sse import ServerSentEvent, aconnect_sse
from pydantic import TypeAdapter, ValidationError

from hueify.credentials import HueBridgeCredentials
from hueify.errors import StreamAuthenticationError
from hueify.models import HueEvent, HueEventMessage
from hueify.sse.bus import EventBus
from hueify.sse.connection import StreamConnection
from hueify.sse.retry import ReconnectPolicy

logger = logging.getLogger(__name__)

_EVENT_MESSAGES = TypeAdapter(list[HueEventMessage])

_REJECTED_KEY_STATUS = frozenset({401, 403})


class ServerSentEventStream:
    """A single connection to the bridge event stream.

    Consuming ends when the bridge closes the stream or the connection breaks;
    recovering from that belongs to the caller.
    """

    def __init__(
        self,
        credentials: HueBridgeCredentials,
        event_bus: EventBus,
        connection: StreamConnection,
        policy: ReconnectPolicy,
    ) -> None:
        self._credentials = credentials
        self._event_bus = event_bus
        self._connection = connection
        self._url = f"https://{credentials.hue_bridge_ip}/eventstream/clip/v2"
        self._timeout = httpx.Timeout(
            connect=policy.connect_timeout,
            read=policy.read_timeout,
            write=policy.connect_timeout,
            pool=policy.connect_timeout,
        )
        self._last_event_id: str | None = None

    async def run_once(self) -> None:
        """Consume events until the stream ends; raises when the connection fails."""
        logger.info("Connecting to event stream at %s", self._credentials.hue_bridge_ip)

        async with (
            httpx.AsyncClient(verify=False, timeout=self._timeout) as client,
            aconnect_sse(
                client=client,
                method="GET",
                url=self._url,
                headers=self._request_headers(),
            ) as event_source,
        ):
            _raise_for_status(event_source.response)
            await self._connection.opened()
            logger.info("Connected to event stream")

            async for sse in event_source.aiter_sse():
                self._connection.record_event()
                self._last_event_id = sse.id or self._last_event_id
                await self._handle_sse(sse)

    def _request_headers(self) -> dict[str, str]:
        headers = {
            "hue-application-key": self._credentials.hue_app_key,
            "Accept": "text/event-stream",
        }
        if self._last_event_id is not None:
            # Standard SSE resume. The bridge replays its short buffer, which
            # closes brief gaps but never guarantees a complete history.
            headers["Last-Event-ID"] = self._last_event_id
        return headers

    async def _handle_sse(self, sse: ServerSentEvent) -> None:
        try:
            messages = _EVENT_MESSAGES.validate_json(sse.data)
        except ValidationError as error:
            logger.warning(f"Failed to parse SSE payload: {error}")
            return

        for message in messages:
            for event in message.data:
                await self._dispatch(event)

    async def _dispatch(self, event: HueEvent) -> None:
        try:
            await self._event_bus.dispatch(event)
        except Exception as e:
            logger.error(f"Error processing event: {e}", exc_info=True)


def _raise_for_status(response: httpx.Response) -> None:
    if response.status_code in _REJECTED_KEY_STATUS:
        raise StreamAuthenticationError(
            f"The bridge rejected the application key (HTTP {response.status_code})"
        )
    response.raise_for_status()
