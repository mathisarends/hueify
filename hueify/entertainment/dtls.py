import asyncio
import logging
import os
import struct
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import IntEnum
from typing import Self

from hueify.entertainment.crypto import (
    RecordAuthenticationError,
    RecordProtection,
    SessionKeys,
)
from hueify.errors import EntertainmentAuthenticationError, EntertainmentError

logger = logging.getLogger(__name__)

ENTERTAINMENT_PORT = 2100

DTLS_1_2 = 0xFEFD

CIPHER_SUITE = b"\x00\xa8"

RECORD_HEADER_LENGTH = 13
HANDSHAKE_HEADER_LENGTH = 12

_FLIGHT_TIMEOUT = 1.0

_FLIGHT_ATTEMPTS = 4
_SERVER_FINISHED_TIMEOUT = 1.0
_RANDOM_LENGTH = 32
_NO_SESSION_ID = b"\x00"
_NULL_COMPRESSION_METHOD = b"\x01\x00"

type _SendFlight = Callable[[], None]


class ContentType(IntEnum):
    CHANGE_CIPHER_SPEC = 20
    ALERT = 21
    HANDSHAKE = 22
    APPLICATION_DATA = 23


class HandshakeType(IntEnum):
    CLIENT_HELLO = 1
    SERVER_HELLO = 2
    HELLO_VERIFY_REQUEST = 3
    SERVER_HELLO_DONE = 14
    CLIENT_KEY_EXCHANGE = 16
    FINISHED = 20


_ALERT_DESCRIPTIONS = {
    0: "close notify",
    10: "unexpected message",
    20: "bad record mac",
    22: "record overflow",
    40: "handshake failure",
    47: "illegal parameter",
    50: "decode error",
    51: "decrypt error",
    70: "protocol version",
    71: "insufficient security",
    80: "internal error",
    86: "inappropriate fallback",
    90: "user cancelled",
    109: "missing extension",
    112: "unrecognized name",
    115: "unknown psk identity",
}

_AUTHENTICATION_ALERTS = frozenset({20, 40, 47, 51, 71, 115})


@dataclass(frozen=True, slots=True)
class Record:
    content_type: int
    epoch: int
    sequence: int
    fragment: bytes


@dataclass(frozen=True, slots=True)
class HandshakeMessage:
    type: int
    message_seq: int
    body: bytes
    raw: bytes


def parse_records(datagram: bytes) -> list[Record]:
    records: list[Record] = []
    offset = 0
    while offset + RECORD_HEADER_LENGTH <= len(datagram):
        length = int.from_bytes(datagram[offset + 11 : offset + 13], "big")
        start = offset + RECORD_HEADER_LENGTH
        end = start + length
        if end > len(datagram):
            logger.debug("Discarding a truncated DTLS record of %d bytes", length)
            break
        records.append(
            Record(
                content_type=datagram[offset],
                epoch=int.from_bytes(datagram[offset + 3 : offset + 5], "big"),
                sequence=int.from_bytes(datagram[offset + 5 : offset + 11], "big"),
                fragment=datagram[start:end],
            )
        )
        offset = end
    return records


def parse_handshake_messages(fragment: bytes) -> list[HandshakeMessage]:
    messages: list[HandshakeMessage] = []
    offset = 0
    while offset + HANDSHAKE_HEADER_LENGTH <= len(fragment):
        length = int.from_bytes(fragment[offset + 1 : offset + 4], "big")
        fragment_offset = int.from_bytes(fragment[offset + 6 : offset + 9], "big")
        fragment_length = int.from_bytes(fragment[offset + 9 : offset + 12], "big")
        if fragment_offset != 0 or fragment_length != length:
            raise EntertainmentError(
                "The bridge fragmented its DTLS handshake, which hueify does not "
                "reassemble"
            )

        end = offset + HANDSHAKE_HEADER_LENGTH + length
        if end > len(fragment):
            logger.debug("Discarding a truncated handshake message")
            break
        messages.append(
            HandshakeMessage(
                type=fragment[offset],
                message_seq=int.from_bytes(fragment[offset + 4 : offset + 6], "big"),
                body=fragment[offset + HANDSHAKE_HEADER_LENGTH : end],
                raw=fragment[offset:end],
            )
        )
        offset = end
    return messages


class DtlsPskConnection:
    """A DTLS 1.2 PSK connection to the entertainment endpoint."""

    def __init__(
        self,
        transport: asyncio.DatagramTransport,
        datagrams: "_Datagrams",
        identity: bytes,
        psk: bytes,
    ) -> None:
        self._transport = transport
        self._datagrams = datagrams
        self._identity = identity
        self._psk = psk

        self._epoch = 0
        self._send_sequence = 0
        self._message_seq = 0
        self._transcript = bytearray()
        self._keys: SessionKeys | None = None
        self._protection: RecordProtection | None = None
        self._server_protection: RecordProtection | None = None
        self._closed = False
        self._error: Exception | None = None
        self._watcher: asyncio.Task[None] | None = None

    @property
    def _peer(self) -> str:
        peername = self._transport.get_extra_info("peername")
        if isinstance(peername, tuple):
            host, port, *_ = peername
            return f"{host}:{port}"
        return "the bridge"

    @classmethod
    async def connect(
        cls,
        host: str,
        identity: str,
        client_key: str,
        port: int = ENTERTAINMENT_PORT,
    ) -> Self:
        psk = _decoded_client_key(client_key)
        loop = asyncio.get_running_loop()
        transport, datagrams = await loop.create_datagram_endpoint(
            _Datagrams, remote_addr=(host, port)
        )
        connection = cls(transport, datagrams, identity.encode("utf-8"), psk)
        try:
            await connection._handshake()
        except BaseException:
            transport.close()
            raise
        connection._watch()
        return connection

    @property
    def closed(self) -> bool:
        return self._closed

    @property
    def error(self) -> Exception | None:
        return self._error

    def send(self, payload: bytes) -> None:
        if self._error is not None:
            raise EntertainmentError(
                f"The DTLS connection failed: {self._error}"
            ) from self._error
        if self._closed:
            raise EntertainmentError("The DTLS connection is closed")
        self._send_record(ContentType.APPLICATION_DATA, payload)

    def close(self) -> None:
        self._closed = True
        if self._watcher is not None:
            self._watcher.cancel()
            self._watcher = None
        self._transport.close()

    async def _handshake(self) -> None:
        client_random = _handshake_random()
        cookie = await self._request_cookie(client_random)
        server_random = await self._exchange_hello(client_random, cookie)

        self._keys = SessionKeys.derive(self._psk, client_random, server_random)
        self._send_client_flight()
        await self._verify_server_finished()
        logger.debug("DTLS handshake complete")

    async def _request_cookie(self, client_random: bytes) -> bytes:
        def send() -> None:
            self._message_seq = 0
            self._send_handshake(
                HandshakeType.CLIENT_HELLO,
                _client_hello(client_random, cookie=b""),
                transcript=False,
            )

        messages = await self._flight(send, {HandshakeType.HELLO_VERIFY_REQUEST})
        return _parse_cookie(messages[HandshakeType.HELLO_VERIFY_REQUEST].body)

    async def _exchange_hello(self, client_random: bytes, cookie: bytes) -> bytes:
        def send() -> None:
            # RFC 6347: the repeated hello continues the sequence at one and is
            # the first message of the transcript.
            self._message_seq = 1
            self._transcript.clear()
            self._send_handshake(
                HandshakeType.CLIENT_HELLO, _client_hello(client_random, cookie)
            )

        messages = await self._flight(
            send, {HandshakeType.SERVER_HELLO, HandshakeType.SERVER_HELLO_DONE}
        )
        return _parse_server_random(messages[HandshakeType.SERVER_HELLO].body)

    def _send_client_flight(self) -> None:
        assert self._keys is not None

        self._send_handshake(
            HandshakeType.CLIENT_KEY_EXCHANGE, _client_key_exchange(self._identity)
        )
        self._send_record(ContentType.CHANGE_CIPHER_SPEC, b"\x01")

        self._protection = self._keys.client_protection()
        self._server_protection = self._keys.server_protection()
        self._epoch += 1
        self._send_sequence = 0

        self._send_handshake(
            HandshakeType.FINISHED,
            self._keys.client_finished(bytes(self._transcript)),
        )

    async def _verify_server_finished(self) -> None:
        assert self._keys is not None
        expected = self._keys.server_finished(bytes(self._transcript))
        try:
            async with asyncio.timeout(_SERVER_FINISHED_TIMEOUT):
                while True:
                    messages = self._read_handshake(await self._receive())
                    finished = messages.get(HandshakeType.FINISHED)
                    if finished is None:
                        continue
                    if finished.body != expected:
                        raise EntertainmentAuthenticationError(
                            "The bridge finished the DTLS handshake with a different "
                            "client key than the one hueify used"
                        )
                    return
        except TimeoutError:
            logger.debug("The bridge did not send its Finished message; continuing")

    async def _flight(
        self,
        send: "_SendFlight",
        wanted: set[HandshakeType],
    ) -> dict[int, HandshakeMessage]:
        collected: dict[int, HandshakeMessage] = {}
        for attempt in range(_FLIGHT_ATTEMPTS):
            collected.clear()
            send()
            try:
                async with asyncio.timeout(_FLIGHT_TIMEOUT * 2**attempt):
                    while not wanted <= collected.keys():
                        collected.update(self._read_handshake(await self._receive()))
                return collected
            except TimeoutError:
                logger.debug(
                    "DTLS flight %d/%d timed out waiting for %s",
                    attempt + 1,
                    _FLIGHT_ATTEMPTS,
                    ", ".join(sorted(_name(message) for message in wanted)),
                )

        raise EntertainmentError(
            f"The bridge did not answer the DTLS handshake on {self._peer}. "
            "Streaming has to be started on the entertainment area first, and "
            "only one application at a time can stream to it."
        )

    def _send_handshake(
        self, message_type: HandshakeType, body: bytes, transcript: bool = True
    ) -> None:
        header = struct.pack(
            "!B3sH3s3s",
            message_type,
            len(body).to_bytes(3, "big"),
            self._message_seq,
            b"\x00\x00\x00",  # fragment offset
            len(body).to_bytes(3, "big"),  # fragment length
        )
        message = header + body
        self._message_seq += 1
        if transcript:
            self._transcript.extend(message)
        self._send_record(ContentType.HANDSHAKE, message)

    def _send_record(self, content_type: ContentType, payload: bytes) -> None:
        fragment = (
            payload
            if self._protection is None
            else self._protection.protect(
                content_type, self._epoch, self._send_sequence, payload
            )
        )
        header = struct.pack(
            "!BHH6sH",
            content_type,
            DTLS_1_2,
            self._epoch,
            self._send_sequence.to_bytes(6, "big"),
            len(fragment),
        )
        self._transport.sendto(header + fragment)
        self._send_sequence += 1

    async def _receive(self) -> bytes:
        datagram = await self._datagrams.received.get()
        if datagram is None:
            raise EntertainmentError(
                f"The bridge is not reachable on UDP port {ENTERTAINMENT_PORT}: "
                f"{self._datagrams.failure}"
            )
        return datagram

    def _read_handshake(self, datagram: bytes) -> dict[int, HandshakeMessage]:
        messages: dict[int, HandshakeMessage] = {}
        for record in parse_records(datagram):
            fragment = self._unprotect(record)
            if fragment is None:
                continue
            if record.content_type == ContentType.ALERT:
                raise _alert_error(fragment)
            if record.content_type != ContentType.HANDSHAKE:
                continue

            for message in parse_handshake_messages(fragment):
                if message.type in messages:
                    continue
                messages[message.type] = message
                # DTLS starts the transcript after its stateless cookie exchange.
                if message.type != HandshakeType.HELLO_VERIFY_REQUEST:
                    self._transcript.extend(message.raw)
        return messages

    def _unprotect(self, record: Record) -> bytes | None:
        if record.epoch == 0:
            return record.fragment
        if self._server_protection is None:
            return None
        try:
            return self._server_protection.unprotect(
                record.content_type, record.fragment
            )
        except RecordAuthenticationError as error:
            raise EntertainmentAuthenticationError(
                "The bridge encrypted its answer with a different client key than "
                "the one hueify used"
            ) from error
        except ValueError as error:
            logger.debug("Discarding an unreadable DTLS record: %s", error)
            return None

    def _watch(self) -> None:
        self._watcher = asyncio.create_task(self._watch_for_alerts())

    async def _watch_for_alerts(self) -> None:
        try:
            while True:
                datagram = await self._receive()
                for record in parse_records(datagram):
                    if record.content_type != ContentType.ALERT:
                        continue
                    fragment = self._unprotect(record)
                    if fragment is not None:
                        raise _alert_error(fragment)
        except asyncio.CancelledError:
            raise
        except Exception as error:
            self._error = error
            self._closed = True
            logger.info("The bridge ended the entertainment stream: %s", error)


class _Datagrams(asyncio.DatagramProtocol):
    def __init__(self) -> None:
        self.received: asyncio.Queue[bytes | None] = asyncio.Queue()
        self.failure: OSError | None = None

    def datagram_received(self, data: bytes, addr: object) -> None:
        self.received.put_nowait(data)

    def error_received(self, exc: Exception) -> None:
        if isinstance(exc, OSError):
            self.failure = exc
        self.received.put_nowait(None)

    def connection_lost(self, exc: Exception | None) -> None:
        if isinstance(exc, OSError):
            self.failure = exc
        self.received.put_nowait(None)


def _client_hello(client_random: bytes, cookie: bytes) -> bytes:
    hello = bytearray(DTLS_1_2.to_bytes(2, "big"))
    hello.extend(client_random)
    hello.extend(_NO_SESSION_ID)
    hello.append(len(cookie))
    hello.extend(cookie)
    hello.extend(struct.pack("!H", len(CIPHER_SUITE)))
    hello.extend(CIPHER_SUITE)
    hello.extend(_NULL_COMPRESSION_METHOD)
    return bytes(hello)


def _client_key_exchange(identity: bytes) -> bytes:
    return struct.pack("!H", len(identity)) + identity


def _parse_cookie(hello_verify_request: bytes) -> bytes:
    length = hello_verify_request[2]
    return hello_verify_request[3 : 3 + length]


def _parse_server_random(server_hello: bytes) -> bytes:
    return server_hello[2 : 2 + _RANDOM_LENGTH]


def _alert_error(fragment: bytes) -> EntertainmentError:
    if len(fragment) < 2:
        return EntertainmentError("The bridge sent an unreadable DTLS alert")

    description = fragment[1]
    name = _ALERT_DESCRIPTIONS.get(description, f"alert {description}")
    if description in _AUTHENTICATION_ALERTS:
        return EntertainmentAuthenticationError(
            f"The bridge rejected the client key: {name}. HUE_CLIENT_KEY has to "
            "come from the same registration as HUE_APP_KEY - the bridge keeps "
            "one client key per application key, so a key left over from an "
            "earlier `hueify setup` fails exactly like a wrong one."
        )
    return EntertainmentError(f"The bridge ended the DTLS connection: {name}")


def _decoded_client_key(client_key: str) -> bytes:
    try:
        return bytes.fromhex(client_key)
    except ValueError as error:
        raise EntertainmentError(
            "The Hue client key must be hexadecimal, as the bridge printed it"
        ) from error


def _handshake_random() -> bytes:
    return struct.pack("!I", int(time.time())) + os.urandom(_RANDOM_LENGTH - 4)


def _name(message_type: HandshakeType) -> str:
    return message_type.name.lower().replace("_", " ")
