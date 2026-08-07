import asyncio

import pytest
from conftest import (
    APP_KEY,
    CLIENT_KEY,
    CLOSE_NOTIFY,
    FATAL,
    INTERNAL_ERROR,
    FakeBridge,
    unpack_record_header,
)

from hueify.entertainment.dtls import (
    CIPHER_SUITE,
    HANDSHAKE_HEADER_LENGTH,
    RECORD_HEADER_LENGTH,
    ContentType,
    DtlsPskConnection,
    HandshakeType,
    parse_handshake_messages,
    parse_records,
)
from hueify.errors import EntertainmentAuthenticationError, EntertainmentError

DTLS_1_2_ON_THE_WIRE = 0xFEFD
RANDOM_LENGTH = 32


async def first_client_hello() -> bytes:
    """The first datagram a connect attempt puts on the wire, against a deaf peer."""
    received: asyncio.Queue[bytes] = asyncio.Queue()

    class Deaf(asyncio.DatagramProtocol):
        def datagram_received(self, data: bytes, addr: object) -> None:
            received.put_nowait(data)

    loop = asyncio.get_running_loop()
    transport, _ = await loop.create_datagram_endpoint(
        Deaf, local_addr=("127.0.0.1", 0)
    )
    port = transport.get_extra_info("socket").getsockname()[1]
    connecting = asyncio.create_task(
        DtlsPskConnection.connect("127.0.0.1", APP_KEY, CLIENT_KEY, port)
    )
    try:
        return await asyncio.wait_for(received.get(), timeout=2)
    finally:
        connecting.cancel()
        await asyncio.gather(connecting, return_exceptions=True)
        transport.close()


def record(content_type: int, epoch: int, sequence: int, fragment: bytes) -> bytes:
    return (
        bytes([content_type])
        + b"\xfe\xfd"
        + epoch.to_bytes(2, "big")
        + sequence.to_bytes(6, "big")
        + len(fragment).to_bytes(2, "big")
        + fragment
    )


def handshake_message(message_type: int, message_seq: int, body: bytes) -> bytes:
    return (
        bytes([message_type])
        + len(body).to_bytes(3, "big")
        + message_seq.to_bytes(2, "big")
        + (0).to_bytes(3, "big")
        + len(body).to_bytes(3, "big")
        + body
    )


class TestParseRecords:
    def test_reads_the_fields_of_one_record(self) -> None:
        [parsed] = parse_records(record(ContentType.ALERT, 1, 258, b"\x02\x28"))

        assert parsed.content_type == ContentType.ALERT
        assert parsed.epoch == 1
        assert parsed.sequence == 258
        assert parsed.fragment == b"\x02\x28"

    def test_splits_records_that_share_one_datagram(self) -> None:
        datagram = record(ContentType.HANDSHAKE, 0, 0, b"first") + record(
            ContentType.HANDSHAKE, 0, 1, b"second"
        )

        assert [parsed.fragment for parsed in parse_records(datagram)] == [
            b"first",
            b"second",
        ]

    def test_drops_a_record_that_claims_more_than_arrived(self) -> None:
        truncated = record(ContentType.HANDSHAKE, 0, 0, b"payload")[:-3]

        assert parse_records(truncated) == []

    def test_ignores_trailing_bytes_that_cannot_hold_a_header(self) -> None:
        datagram = record(ContentType.HANDSHAKE, 0, 0, b"payload") + b"\x16\x00"

        assert len(parse_records(datagram)) == 1


class TestParseHandshakeMessages:
    def test_reads_the_messages_of_one_fragment(self) -> None:
        fragment = handshake_message(
            HandshakeType.SERVER_HELLO, 1, b"body"
        ) + handshake_message(HandshakeType.SERVER_HELLO_DONE, 2, b"")

        first, second = parse_handshake_messages(fragment)

        assert (first.type, first.message_seq, first.body) == (
            HandshakeType.SERVER_HELLO,
            1,
            b"body",
        )
        assert second.type == HandshakeType.SERVER_HELLO_DONE
        assert second.raw == handshake_message(HandshakeType.SERVER_HELLO_DONE, 2, b"")

    def test_refuses_a_message_split_across_records(self) -> None:
        fragmented = bytearray(
            handshake_message(HandshakeType.SERVER_HELLO, 1, b"body")
        )
        fragmented[11] = 2  # fragment_length shorter than the message

        with pytest.raises(EntertainmentError, match="fragmented"):
            parse_handshake_messages(bytes(fragmented))

    def test_drops_a_message_that_claims_more_than_arrived(self) -> None:
        truncated = handshake_message(HandshakeType.SERVER_HELLO, 1, b"body")[:-2]

        assert parse_handshake_messages(truncated) == []


class TestClientHelloOnTheWire:
    """Pins the bytes the bridge has to recognize, without a peer to parse them."""

    @pytest.mark.asyncio
    async def test_is_one_dtls_1_2_handshake_record(self) -> None:
        first_datagram = await first_client_hello()

        content_type, version, epoch, sequence, length = unpack_record_header(
            first_datagram
        )

        assert content_type == ContentType.HANDSHAKE
        assert version == DTLS_1_2_ON_THE_WIRE
        assert (epoch, sequence) == (0, 0)
        assert length == len(first_datagram) - RECORD_HEADER_LENGTH

    @pytest.mark.asyncio
    async def test_offers_only_the_suite_the_bridge_speaks(self) -> None:
        first_datagram = await first_client_hello()

        body = first_datagram[RECORD_HEADER_LENGTH + HANDSHAKE_HEADER_LENGTH :]
        cookie_length = body[2 + RANDOM_LENGTH + 1]
        suites_at = 2 + RANDOM_LENGTH + 2 + cookie_length

        assert body[:2] == b"\xfe\xfd"  # client version
        assert cookie_length == 0  # the first hello has no cookie yet
        assert body[suites_at : suites_at + 2] == b"\x00\x02"  # two bytes of suites
        assert body[suites_at + 2 : suites_at + 4] == CIPHER_SUITE
        assert body[suites_at + 4 :] == b"\x01\x00"  # one compression method: none

    @pytest.mark.asyncio
    async def test_the_handshake_starts_at_message_zero(self) -> None:
        first_datagram = await first_client_hello()

        message = first_datagram[RECORD_HEADER_LENGTH:]

        assert message[0] == HandshakeType.CLIENT_HELLO
        assert message[4:6] == b"\x00\x00"  # message_seq
        assert message[6:9] == b"\x00\x00\x00"  # fragment offset


class TestHandshake:
    @pytest.mark.asyncio
    async def test_completes_against_a_bridge_and_carries_frames(self) -> None:
        bridge, port = await FakeBridge.listening()
        try:
            connection = await DtlsPskConnection.connect(
                "127.0.0.1", APP_KEY, CLIENT_KEY, port
            )
            connection.send(b"the-first-frame")
            frames = await bridge.wait_for_frames(1)
        finally:
            bridge.close()

        assert bridge.client_finished_verified is True
        assert bridge.identity == APP_KEY.encode()
        assert frames == [b"the-first-frame"]
        assert connection.error is None
        connection.close()

    @pytest.mark.asyncio
    async def test_sends_frames_in_order_and_unchanged(self) -> None:
        bridge, port = await FakeBridge.listening()
        try:
            connection = await DtlsPskConnection.connect(
                "127.0.0.1", APP_KEY, CLIENT_KEY, port
            )
            for index in range(5):
                connection.send(f"frame-{index}".encode())
            frames = await bridge.wait_for_frames(5)
            connection.close()
        finally:
            bridge.close()

        assert frames == [f"frame-{index}".encode() for index in range(5)]

    @pytest.mark.asyncio
    async def test_resends_a_hello_the_bridge_never_answered(
        self, impatient_handshake: None
    ) -> None:
        bridge, port = await FakeBridge.listening(hellos_to_drop=1)
        try:
            connection = await DtlsPskConnection.connect(
                "127.0.0.1", APP_KEY, CLIENT_KEY, port
            )
        finally:
            bridge.close()

        assert bridge.client_finished_verified is True
        connection.close()

    @pytest.mark.asyncio
    async def test_a_client_key_the_bridge_does_not_share_is_reported_as_such(
        self, impatient_handshake: None
    ) -> None:
        """A key left over from an earlier registration looks exactly like this.

        The bridge keeps one client key per application key, finds the identity,
        derives a session from the *other* key and cannot read the client's
        Finished - so the message has to name the pairing, not just the key.
        """
        bridge, port = await FakeBridge.listening(client_key="ff" * 16)
        try:
            with pytest.raises(EntertainmentAuthenticationError) as error:
                await DtlsPskConnection.connect("127.0.0.1", APP_KEY, CLIENT_KEY, port)
        finally:
            bridge.close()

        assert "bad record mac" in str(error.value)
        assert "HUE_CLIENT_KEY" in str(error.value)
        assert "HUE_APP_KEY" in str(error.value)

    @pytest.mark.asyncio
    async def test_a_silent_bridge_names_the_likely_reason(
        self, impatient_handshake: None
    ) -> None:
        loop = asyncio.get_running_loop()
        transport, _ = await loop.create_datagram_endpoint(
            asyncio.DatagramProtocol, local_addr=("127.0.0.1", 0)
        )
        port = transport.get_extra_info("socket").getsockname()[1]
        try:
            with pytest.raises(EntertainmentError, match="Streaming has to be started"):
                await DtlsPskConnection.connect("127.0.0.1", APP_KEY, CLIENT_KEY, port)
        finally:
            transport.close()

    @pytest.mark.asyncio
    async def test_a_client_key_that_is_not_hexadecimal_is_refused(self) -> None:
        with pytest.raises(EntertainmentError, match="hexadecimal"):
            await DtlsPskConnection.connect("127.0.0.1", APP_KEY, "not-a-key", 2100)

    @pytest.mark.asyncio
    async def test_a_port_nobody_listens_on_fails_without_retrying_forever(
        self, impatient_handshake: None
    ) -> None:
        with pytest.raises(EntertainmentError):
            await DtlsPskConnection.connect("127.0.0.1", APP_KEY, CLIENT_KEY, 1)


class TestAfterTheHandshake:
    @pytest.mark.asyncio
    async def test_an_alert_from_the_bridge_ends_the_connection(self) -> None:
        bridge, port = await FakeBridge.listening(alert_after_handshake=INTERNAL_ERROR)
        try:
            connection = await DtlsPskConnection.connect(
                "127.0.0.1", APP_KEY, CLIENT_KEY, port
            )
            await asyncio.sleep(0.05)
        finally:
            bridge.close()

        assert isinstance(connection.error, EntertainmentError)
        assert "internal error" in str(connection.error)
        assert connection.closed

        with pytest.raises(EntertainmentError, match="internal error"):
            connection.send(b"frame")

    @pytest.mark.asyncio
    async def test_a_closed_connection_refuses_to_send(self) -> None:
        bridge, port = await FakeBridge.listening()
        try:
            connection = await DtlsPskConnection.connect(
                "127.0.0.1", APP_KEY, CLIENT_KEY, port
            )
            connection.close()

            with pytest.raises(EntertainmentError, match="closed"):
                connection.send(b"frame")
        finally:
            bridge.close()

    @pytest.mark.asyncio
    async def test_closing_twice_is_harmless(self) -> None:
        bridge, port = await FakeBridge.listening()
        try:
            connection = await DtlsPskConnection.connect(
                "127.0.0.1", APP_KEY, CLIENT_KEY, port
            )
            connection.close()
            connection.close()
        finally:
            bridge.close()

    @pytest.mark.asyncio
    async def test_a_close_notify_is_not_read_as_a_rejected_key(self) -> None:
        bridge, port = await FakeBridge.listening(alert_after_handshake=CLOSE_NOTIFY)
        try:
            connection = await DtlsPskConnection.connect(
                "127.0.0.1", APP_KEY, CLIENT_KEY, port
            )
            await asyncio.sleep(0.05)
        finally:
            bridge.close()

        assert isinstance(connection.error, EntertainmentError)
        assert not isinstance(connection.error, EntertainmentAuthenticationError)
        assert "close notify" in str(connection.error)


class TestFakeBridgeIsNotFoolingItself:
    """The peer has to be a peer: unreadable records make it complain."""

    @pytest.mark.asyncio
    async def test_it_notices_records_it_cannot_decrypt(self) -> None:
        bridge, port = await FakeBridge.listening()
        try:
            connection = await DtlsPskConnection.connect(
                "127.0.0.1", APP_KEY, CLIENT_KEY, port
            )
            await bridge.wait_for_frames(0)

            assert FATAL not in bridge.alerts_received
            connection.close()
        finally:
            bridge.close()
