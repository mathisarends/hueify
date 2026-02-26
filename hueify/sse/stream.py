import json
import logging

import httpx
from httpx_sse import ServerSentEvent, aconnect_sse
from pydantic import TypeAdapter

from hueify.credentials import HueBridgeCredentials
from hueify.sse.bus import EventBus
from hueify.sse.views import HueEvent, UnknownEvent

logger = logging.getLogger(__name__)

_event_adapter = TypeAdapter(HueEvent | UnknownEvent)


class ServerSentEventStream:
    def __init__(self, credentials: HueBridgeCredentials, event_bus: EventBus) -> None:
        self._credentials = credentials
        self._event_bus = event_bus
        self._is_running = False
        self._url = f"https://{self._credentials.hue_bridge_ip}/eventstream/clip/v2"
        self._headers = {
            "hue-application-key": self._credentials.hue_app_key,
            "Accept": "text/event-stream",
        }

    async def connect(self) -> None:
        self._is_running = True
        logger.info(f"Connecting to event stream at {self._credentials.hue_bridge_ip}")

        try:
            async with (
                httpx.AsyncClient(verify=False, timeout=None) as client,
                aconnect_sse(
                    client=client,
                    method="GET",
                    url=self._url,
                    headers=self._headers,
                ) as event_source,
            ):
                logger.info("Connected to event stream")

                async for sse in event_source.aiter_sse():
                    if not self._is_running:
                        break
                    await self._handle_sse(sse)

        except Exception as e:
            logger.error(f"Event stream error: {e}", exc_info=True)
        finally:
            logger.info("Disconnected from event stream")

    async def _handle_sse(self, sse: ServerSentEvent) -> None:
        try:
            containers: list[dict] = json.loads(sse.data)

            for container in containers:
                for raw_event in container.get("data", []):
                    event = _event_adapter.validate_python(raw_event)
                    await self._event_bus.dispatch(event)

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse SSE payload: {e}")
        except Exception as e:
            logger.error(f"Error processing event: {e}", exc_info=True)

    def disconnect(self) -> None:
        self._is_running = False
        logger.info("Stopping event stream")
