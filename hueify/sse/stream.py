import asyncio
import json
from collections.abc import Callable
from functools import cached_property

import httpx
from httpx_sse import ServerSentEvent, aconnect_sse

from hueify.credentials.service import HueBridgeCredentials
from hueify.http import HttpMethods
from hueify.sse.models import Event
from hueify.utils.logging import LoggingMixin


class EventStream(LoggingMixin):
    def __init__(self, credentials: HueBridgeCredentials | None = None) -> None:
        self._credentials = credentials or HueBridgeCredentials()
        self._is_running = False
        self._event_handlers: list[Callable[[Event], None]] = []

    @cached_property
    def url(self) -> str:
        return f"https://{self._credentials.hue_bridge_ip}/eventstream/clip/v2"

    def register_event_handler(self, handler: Callable[[Event], None]) -> None:
        self._event_handlers.append(handler)

    async def connect(self) -> None:
        self._is_running = True
        self.logger.info(
            f"Connecting to event stream at {self._credentials.hue_bridge_ip}"
        )

        headers = {
            "hue-application-key": self._credentials.hue_app_key,
            "Accept": "text/event-stream",
        }

        try:
            async with (
                httpx.AsyncClient(verify=False, timeout=None) as client,
                aconnect_sse(
                    client=client, method=HttpMethods.GET, url=self.url, headers=headers
                ) as event_source,
            ):
                self.logger.info("Connected to event stream")

                async for sse in event_source.aiter_sse():
                    if not self._is_running:
                        break

                    await self._process_server_sent_event(sse)

        except Exception as e:
            self.logger.error(f"Event stream error: {e}", exc_info=True)
        finally:
            self.logger.info("Disconnected from event stream")

    async def _process_server_sent_event(self, sse: ServerSentEvent) -> None:
        try:
            raw_data = json.loads(sse.data)

            event = Event.from_sse_data(raw_data)

            for event_data in event.events:
                for handler in self._event_handlers:
                    await self._invoke_handler(handler, event_data)

        except json.JSONDecodeError as e:
            self.logger.warning(f"Failed to parse event: {e}")
        except Exception as e:
            self.logger.error(f"Error processing event: {e}", exc_info=True)

    async def _invoke_handler(
        self, handler: Callable[[Event], None], event: Event
    ) -> None:
        try:
            if asyncio.iscoroutinefunction(handler):
                await handler(event)
            else:
                handler(event)
        except Exception as e:
            self.logger.error(f"Error in event handler: {e}", exc_info=True)

    def disconnect(self) -> None:
        self._is_running = False
        self.logger.info("Stopping event stream")
