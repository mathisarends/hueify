"""A UDP peer that answers the DTLS handshake the way a bridge does.

Written from the specification rather than from ``dtls.py``: it frames its own
records byte by byte and derives its own keys, so the two implementations have
to agree on the wire, not merely on a shared helper.
"""

import asyncio
import struct
from typing import Self

import pytest

from hueify.entertainment.crypto import (
    RecordAuthenticationError,
    RecordProtection,
    SessionKeys,
)
from hueify.entertainment.dtls import (
    CIPHER_SUITE,
    ContentType,
    HandshakeType,
    Record,
    parse_handshake_messages,
    parse_records,
)

CLIENT_KEY = "0123456789abcdef0123456789abcdef"
APP_KEY = "the-app-key-that-is-long-enough"
COOKIE = bytes.fromhex("cafebabe")
RANDOM_LENGTH = 32

CLOSE_NOTIFY = 0
BAD_RECORD_MAC = 20
INTERNAL_ERROR = 80
FATAL = 2


class FakeBridge(asyncio.DatagramProtocol):
    """The server half of a DTLS 1.2 PSK handshake, and what arrived after it.

    Args:
        client_key: The key it derives its own session from. A different one
            than the client uses makes it behave like a bridge that was given
            the wrong client key.
        hellos_to_drop: How many client hellos to swallow, so retransmission
            can be exercised.
        alert_after_handshake: An alert to send once streaming has started.
    """

    def __init__(
        self,
        client_key: str = CLIENT_KEY,
        hellos_to_drop: int = 0,
        alert_after_handshake: int | None = None,
    ) -> None:
        self._psk = bytes.fromhex(client_key)
        self._hellos_to_drop = hellos_to_drop
        self._alert_after_handshake = alert_after_handshake

        self.frames: list[bytes] = []
        self.identity: bytes | None = None
        self.client_finished_verified: bool | None = None
        self.alerts_received: list[int] = []
        self.handshake_complete = asyncio.Event()
        self.frame_received = asyncio.Event()

        self._transport: asyncio.DatagramTransport | None = None
        self._peer: object = None
        self._transcript = bytearray()
        self._server_random = bytes(range(100, 100 + RANDOM_LENGTH))
        self._keys: SessionKeys | None = None
        self._client_protection: RecordProtection | None = None
        self._server_protection: RecordProtection | None = None
        self._epoch = 0
        self._sequence = 0
        self._message_seq = 0

    @classmethod
    async def listening(cls, **kwargs: object) -> tuple[Self, int]:
        """Start on a free port and return the peer and that port."""
        loop = asyncio.get_running_loop()
        bridge = cls(**kwargs)  # type: ignore[arg-type]
        transport, _ = await loop.create_datagram_endpoint(
            lambda: bridge, local_addr=("127.0.0.1", 0)
        )
        return bridge, transport.get_extra_info("socket").getsockname()[1]

    def close(self) -> None:
        if self._transport is not None:
            self._transport.close()

    async def wait_for_frames(self, count: int, timeout: float = 2.0) -> list[bytes]:
        """Wait until ``count`` frames arrived, and return them."""
        async with asyncio.timeout(timeout):
            while len(self.frames) < count:
                self.frame_received.clear()
                await self.frame_received.wait()
        return list(self.frames)

    # -- asyncio.DatagramProtocol --

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        assert isinstance(transport, asyncio.DatagramTransport)
        self._transport = transport

    def datagram_received(self, data: bytes, addr: object) -> None:
        self._peer = addr
        for record in parse_records(data):
            fragment = self._read(record)
            if fragment is None:
                continue
            if record.content_type == ContentType.HANDSHAKE:
                for message in parse_handshake_messages(fragment):
                    self._handle_handshake(message.type, message.body, message.raw)
            elif record.content_type == ContentType.ALERT:
                self.alerts_received.append(fragment[1])
            elif record.content_type == ContentType.APPLICATION_DATA:
                self.frames.append(fragment)
                self.frame_received.set()

    # -- The handshake --

    def _handle_handshake(self, message_type: int, body: bytes, raw: bytes) -> None:
        if message_type == HandshakeType.CLIENT_HELLO:
            self._handle_client_hello(body, raw)
        elif message_type == HandshakeType.CLIENT_KEY_EXCHANGE:
            self.identity = body[2:]
            self._transcript.extend(raw)
        elif message_type == HandshakeType.FINISHED:
            self._handle_client_finished(body, raw)

    def _handle_client_hello(self, body: bytes, raw: bytes) -> None:
        cookie_length = body[2 + RANDOM_LENGTH + 1]
        if cookie_length == 0:
            self._send_handshake(
                HandshakeType.HELLO_VERIFY_REQUEST,
                b"\xfe\xfd" + bytes([len(COOKIE)]) + COOKIE,
            )
            return

        if self._hellos_to_drop > 0:
            self._hellos_to_drop -= 1
            return

        # A repeated hello starts the transcript over, as the client's does.
        self._transcript = bytearray(raw)
        self._message_seq = 1
        client_random = body[2 : 2 + RANDOM_LENGTH]
        self._keys = SessionKeys.derive(self._psk, client_random, self._server_random)
        self._client_protection = self._keys.client_protection()
        self._server_protection = self._keys.server_protection()

        self._send_handshake(HandshakeType.SERVER_HELLO, self._server_hello())
        self._send_handshake(HandshakeType.SERVER_HELLO_DONE, b"")

    def _handle_client_finished(self, verify_data: bytes, raw: bytes) -> None:
        assert self._keys is not None
        expected = self._keys.client_finished(bytes(self._transcript))
        self.client_finished_verified = verify_data == expected
        if not self.client_finished_verified:
            self._send_alert(BAD_RECORD_MAC)
            return

        self._transcript.extend(raw)
        self._send_record(ContentType.CHANGE_CIPHER_SPEC, b"\x01")
        self._epoch = 1
        self._sequence = 0
        self._send_handshake(
            HandshakeType.FINISHED,
            self._keys.server_finished(bytes(self._transcript)),
        )
        self.handshake_complete.set()
        if self._alert_after_handshake is not None:
            self._send_alert(self._alert_after_handshake)

    def _server_hello(self) -> bytes:
        return (
            b"\xfe\xfd"
            + self._server_random
            + b"\x00"  # no session id
            + CIPHER_SUITE
            + b"\x00"  # no compression
        )

    # -- Framing, spelled out rather than shared with the client --

    def _send_handshake(self, message_type: int, body: bytes) -> None:
        header = (
            bytes([message_type])
            + len(body).to_bytes(3, "big")
            + self._message_seq.to_bytes(2, "big")
            + (0).to_bytes(3, "big")
            + len(body).to_bytes(3, "big")
        )
        message = header + body
        self._message_seq += 1
        if message_type in (
            HandshakeType.SERVER_HELLO,
            HandshakeType.SERVER_HELLO_DONE,
        ):
            self._transcript.extend(message)
        self._send_record(ContentType.HANDSHAKE, message)

    def _send_alert(self, description: int) -> None:
        self._send_record(ContentType.ALERT, bytes([FATAL, description]))

    def _send_record(self, content_type: int, payload: bytes) -> None:
        assert self._transport is not None
        fragment = payload
        if self._epoch > 0:
            assert self._server_protection is not None
            fragment = self._server_protection.protect(
                content_type, self._epoch, self._sequence, payload
            )
        header = (
            bytes([content_type])
            + b"\xfe\xfd"
            + self._epoch.to_bytes(2, "big")
            + self._sequence.to_bytes(6, "big")
            + len(fragment).to_bytes(2, "big")
        )
        self._sequence += 1
        self._transport.sendto(header + fragment, self._peer)

    def _read(self, record: Record) -> bytes | None:
        """The plaintext of a client record, or None if it cannot be read."""
        if record.epoch == 0:
            return record.fragment
        if self._client_protection is None:
            return None
        try:
            return self._client_protection.unprotect(
                record.content_type, record.fragment
            )
        except RecordAuthenticationError:
            # What a bridge does when the client key does not match.
            self._send_alert(BAD_RECORD_MAC)
            return None


@pytest.fixture
def impatient_handshake(monkeypatch: pytest.MonkeyPatch) -> None:
    """Shrink the retransmission timers so a lost flight costs milliseconds."""
    monkeypatch.setattr("hueify.entertainment.dtls._FLIGHT_TIMEOUT", 0.02)
    monkeypatch.setattr("hueify.entertainment.dtls._FLIGHT_ATTEMPTS", 3)
    monkeypatch.setattr("hueify.entertainment.dtls._SERVER_FINISHED_TIMEOUT", 0.2)


def unpack_record_header(datagram: bytes) -> tuple[int, int, int, int, int]:
    """content type, version, epoch, sequence and length of the first record."""
    content_type, version, epoch, sequence_high, sequence_low, length = struct.unpack(
        "!BHHIHH", datagram[:13]
    )
    return content_type, version, epoch, (sequence_high << 16) | sequence_low, length
