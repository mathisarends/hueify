from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from hueify.credentials import HueBridgeCredentials
from hueify.entertainment import EntertainmentNamespace, EntertainmentStream
from hueify.errors import MissingCredentialsError
from hueify.http import HttpClient
from hueify.models import (
    EntertainmentConfiguration,
    HueApiResponse,
    ResourceIdentifier,
    ResourceType,
    StreamingStatus,
)

AREA_ID = uuid4()
CLIENT_KEY = "0123456789abcdef0123456789abcdef"


def area(
    status: StreamingStatus = StreamingStatus.INACTIVE,
) -> EntertainmentConfiguration:
    return EntertainmentConfiguration.model_validate(
        {
            "id": str(AREA_ID),
            "type": "entertainment_configuration",
            "metadata": {"name": "TV"},
            "status": status,
            "channels": [
                {
                    "channel_id": 0,
                    "position": {"x": -0.5, "y": 0.0, "z": 0.5},
                    "members": [],
                }
            ],
        }
    )


@pytest.fixture
def client() -> AsyncMock:
    client = AsyncMock(spec=HttpClient)
    client.put.return_value = HueApiResponse[ResourceIdentifier](
        data=[
            ResourceIdentifier(
                rid=AREA_ID, rtype=ResourceType.ENTERTAINMENT_CONFIGURATION
            )
        ]
    )
    return client


@pytest.fixture
def credentials() -> HueBridgeCredentials:
    return HueBridgeCredentials(
        HUE_BRIDGE_IP="192.168.1.10",
        HUE_APP_KEY="a" * 40,
        HUE_CLIENT_KEY=CLIENT_KEY,
    )


@pytest.fixture
def areas(
    client: AsyncMock, credentials: HueBridgeCredentials
) -> EntertainmentNamespace:
    return EntertainmentNamespace(client, credentials)


def sent_payload(client: AsyncMock) -> tuple[str, dict[str, object]]:
    """The endpoint and the JSON body the namespace handed to the HTTP client."""
    endpoint, data = client.put.await_args.args
    return endpoint, data.model_dump(mode="json", exclude_none=True)


class TestTakingAnAreaOverAndBack:
    @pytest.mark.asyncio
    async def test_start_puts_the_start_action_on_the_area(
        self, areas: EntertainmentNamespace, client: AsyncMock
    ) -> None:
        await areas.start(AREA_ID)

        assert sent_payload(client) == (
            f"entertainment_configuration/{AREA_ID}",
            {"action": "start"},
        )

    @pytest.mark.asyncio
    async def test_stop_puts_the_stop_action_on_the_area(
        self, areas: EntertainmentNamespace, client: AsyncMock
    ) -> None:
        await areas.stop(AREA_ID)

        assert sent_payload(client) == (
            f"entertainment_configuration/{AREA_ID}",
            {"action": "stop"},
        )

    @pytest.mark.asyncio
    async def test_is_streaming_follows_the_status_of_the_area(
        self, areas: EntertainmentNamespace, client: AsyncMock
    ) -> None:
        client.get.return_value = HueApiResponse[EntertainmentConfiguration](
            data=[area(StreamingStatus.ACTIVE)]
        )

        assert await areas.is_streaming(AREA_ID) is True

        client.get.return_value = HueApiResponse[EntertainmentConfiguration](
            data=[area(StreamingStatus.INACTIVE)]
        )

        assert await areas.is_streaming(AREA_ID) is False


class TestOpeningAStream:
    def test_a_stream_touches_nothing_until_it_is_opened(
        self, areas: EntertainmentNamespace, client: AsyncMock
    ) -> None:
        """What makes ``async with hue.entertainment.stream(area)`` possible."""
        stream = areas.stream(area(), rate=25)

        assert isinstance(stream, EntertainmentStream)
        assert stream.rate == 25
        assert not stream.sending
        client.put.assert_not_awaited()
        client.get.assert_not_awaited()

    def test_a_rate_the_bridge_cannot_serve_is_refused_up_front(
        self, areas: EntertainmentNamespace
    ) -> None:
        with pytest.raises(ValueError, match="frames per second"):
            areas.stream(area(), rate=120)

    def test_streaming_without_a_client_key_names_the_setup_command(
        self, client: AsyncMock, without_stored_credentials: None
    ) -> None:
        without_key = HueBridgeCredentials(
            HUE_BRIDGE_IP="192.168.1.10", HUE_APP_KEY="a" * 40
        )

        with pytest.raises(MissingCredentialsError, match="hueify setup"):
            EntertainmentNamespace(client, without_key).stream(area())
