import hashlib as _hashlib
import hmac as _hmac_module
import struct as _struct
from dataclasses import dataclass as _dataclass
from typing import Self as _Self

from cryptography.exceptions import InvalidTag as _InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM as _AESGCM


class RecordAuthenticationError(Exception):
    """A record could not be authenticated with the session key."""


class RecordProtection:
    """Encrypt and authenticate DTLS records in one direction."""

    def __init__(self, key: bytes, implicit_iv: bytes) -> None:
        self._cipher = _AESGCM(key)
        self._implicit_iv = implicit_iv

    def protect(
        self, content_type: int, epoch: int, sequence: int, plaintext: bytes
    ) -> bytes:
        explicit_nonce = _explicit_nonce(epoch, sequence)
        sealed = self._cipher.encrypt(
            self._implicit_iv + explicit_nonce,
            plaintext,
            _additional_data(explicit_nonce, content_type, len(plaintext)),
        )
        return explicit_nonce + sealed

    def unprotect(self, content_type: int, fragment: bytes) -> bytes:
        if len(fragment) < _EXPLICIT_NONCE_LENGTH + _TAG_LENGTH:
            raise ValueError(f"Record fragment is too short: {len(fragment)} bytes")

        explicit_nonce = fragment[:_EXPLICIT_NONCE_LENGTH]
        sealed = fragment[_EXPLICIT_NONCE_LENGTH:]
        plaintext_length = len(sealed) - _TAG_LENGTH
        try:
            return self._cipher.decrypt(
                self._implicit_iv + explicit_nonce,
                sealed,
                _additional_data(explicit_nonce, content_type, plaintext_length),
            )
        except _InvalidTag:
            raise RecordAuthenticationError from None


@_dataclass(frozen=True, slots=True)
class SessionKeys:
    """The secrets and record protection derived for one DTLS session."""

    _master_secret: bytes
    _client_write_key: bytes
    _client_write_iv: bytes
    _server_write_key: bytes
    _server_write_iv: bytes

    @classmethod
    def derive(cls, psk: bytes, client_random: bytes, server_random: bytes) -> _Self:
        master_secret = _prf(
            _psk_premaster_secret(psk),
            _MASTER_SECRET_LABEL,
            client_random + server_random,
            _MASTER_SECRET_LENGTH,
        )
        # TLS deliberately reverses the randoms between these two derivations.
        key_block = _prf(
            master_secret,
            _KEY_EXPANSION_LABEL,
            server_random + client_random,
            _KEY_BLOCK_LENGTH,
        )
        keys = memoryview(key_block)
        client_key_end = _KEY_LENGTH
        server_key_end = 2 * _KEY_LENGTH
        client_iv_end = server_key_end + _IMPLICIT_IV_LENGTH

        return cls(
            _master_secret=master_secret,
            _client_write_key=bytes(keys[:client_key_end]),
            _server_write_key=bytes(keys[client_key_end:server_key_end]),
            _client_write_iv=bytes(keys[server_key_end:client_iv_end]),
            _server_write_iv=bytes(keys[client_iv_end:]),
        )

    def client_finished(self, transcript: bytes) -> bytes:
        return self._finished(_CLIENT_FINISHED_LABEL, transcript)

    def server_finished(self, transcript: bytes) -> bytes:
        return self._finished(_SERVER_FINISHED_LABEL, transcript)

    def client_protection(self) -> RecordProtection:
        return RecordProtection(self._client_write_key, self._client_write_iv)

    def server_protection(self) -> RecordProtection:
        return RecordProtection(self._server_write_key, self._server_write_iv)

    def _finished(self, label: bytes, transcript: bytes) -> bytes:
        return _prf(
            self._master_secret,
            label,
            _hashlib.sha256(transcript).digest(),
            _VERIFY_DATA_LENGTH,
        )


_DTLS_1_2 = 0xFEFD
_KEY_LENGTH = 16
_IMPLICIT_IV_LENGTH = 4
_EXPLICIT_NONCE_LENGTH = 8
_TAG_LENGTH = 16
_MASTER_SECRET_LENGTH = 48
_VERIFY_DATA_LENGTH = 12

_MASTER_SECRET_LABEL = b"master secret"
_KEY_EXPANSION_LABEL = b"key expansion"
_CLIENT_FINISHED_LABEL = b"client finished"
_SERVER_FINISHED_LABEL = b"server finished"

_KEY_BLOCK_LENGTH = 2 * _KEY_LENGTH + 2 * _IMPLICIT_IV_LENGTH


def _prf(secret: bytes, label: bytes, seed: bytes, length: int) -> bytes:
    output = bytearray()
    salt = label + seed
    fragment = _hmac(secret, salt)
    while len(output) < length:
        output.extend(_hmac(secret, fragment + salt))
        fragment = _hmac(secret, fragment)
    return bytes(output[:length])


def _psk_premaster_secret(psk: bytes) -> bytes:
    length = _struct.pack("!H", len(psk))
    return length + bytes(len(psk)) + length + psk


def _explicit_nonce(epoch: int, sequence: int) -> bytes:
    return _struct.pack("!H", epoch) + sequence.to_bytes(6, "big")


def _additional_data(explicit_nonce: bytes, content_type: int, length: int) -> bytes:
    return explicit_nonce + _struct.pack("!BHH", content_type, _DTLS_1_2, length)


def _hmac(key: bytes, message: bytes) -> bytes:
    return _hmac_module.new(key, message, _hashlib.sha256).digest()
