"""Key schedule and record protection for TLS_PSK_WITH_AES_128_GCM_SHA256.

The one cipher suite the Hue bridge accepts needs no certificates and no key
agreement: both sides already share the client key, so the master secret falls
out of the PSK and the two handshake randoms. That makes this module small
enough to be pure, deterministic and fully testable - no sockets, no state
beyond the sequence numbers its caller passes in.

``cryptography`` is imported here and nowhere else, which is what makes
entertainment streaming an optional install.
"""

import hashlib
import hmac
import struct
from dataclasses import dataclass
from typing import Self

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

DTLS_1_2 = 0xFEFD

KEY_LENGTH = 16
IMPLICIT_IV_LENGTH = 4
EXPLICIT_NONCE_LENGTH = 8
TAG_LENGTH = 16
MASTER_SECRET_LENGTH = 48
VERIFY_DATA_LENGTH = 12
RANDOM_LENGTH = 32

CLIENT_FINISHED_LABEL = b"client finished"
SERVER_FINISHED_LABEL = b"server finished"

_KEY_BLOCK_LENGTH = 2 * KEY_LENGTH + 2 * IMPLICIT_IV_LENGTH


def prf(secret: bytes, label: bytes, seed: bytes, length: int) -> bytes:
    """The TLS 1.2 pseudorandom function, P_SHA256 (RFC 5246 section 5)."""
    output = bytearray()
    salt = label + seed
    fragment = _hmac(secret, salt)  # A(1)
    while len(output) < length:
        output.extend(_hmac(secret, fragment + salt))
        fragment = _hmac(secret, fragment)  # A(i + 1)
    return bytes(output[:length])


def psk_premaster_secret(psk: bytes) -> bytes:
    """The premaster secret of a pure PSK exchange (RFC 4279 section 2).

    The other half of the usual key agreement is not there, so its place is
    taken by zeroes of the same length as the key.
    """
    length = struct.pack("!H", len(psk))
    return length + bytes(len(psk)) + length + psk


@dataclass(frozen=True, slots=True)
class SessionKeys:
    """Everything the record layer needs, derived once per handshake."""

    master_secret: bytes
    client_write_key: bytes
    client_write_iv: bytes
    server_write_key: bytes
    server_write_iv: bytes

    @classmethod
    def derive(cls, psk: bytes, client_random: bytes, server_random: bytes) -> Self:
        master_secret = prf(
            psk_premaster_secret(psk),
            b"master secret",
            client_random + server_random,
            MASTER_SECRET_LENGTH,
        )
        # Note the reversed randoms: key expansion is seeded server first.
        key_block = prf(
            master_secret,
            b"key expansion",
            server_random + client_random,
            _KEY_BLOCK_LENGTH,
        )
        keys = memoryview(key_block)
        return cls(
            master_secret=master_secret,
            client_write_key=bytes(keys[:KEY_LENGTH]),
            server_write_key=bytes(keys[KEY_LENGTH : 2 * KEY_LENGTH]),
            client_write_iv=bytes(
                keys[2 * KEY_LENGTH : 2 * KEY_LENGTH + IMPLICIT_IV_LENGTH]
            ),
            server_write_iv=bytes(keys[2 * KEY_LENGTH + IMPLICIT_IV_LENGTH :]),
        )

    def verify_data(self, label: bytes, transcript: bytes) -> bytes:
        """The ``Finished`` payload proving both sides saw the same handshake."""
        return prf(
            self.master_secret,
            label,
            hashlib.sha256(transcript).digest(),
            VERIFY_DATA_LENGTH,
        )

    def client_protection(self) -> "RecordProtection":
        """Protection for the records this side writes."""
        return RecordProtection(self.client_write_key, self.client_write_iv)

    def server_protection(self) -> "RecordProtection":
        """Protection for the records the bridge writes."""
        return RecordProtection(self.server_write_key, self.server_write_iv)


class RecordProtection:
    """AES-128-GCM in one direction, as TLS 1.2 wires it up for DTLS.

    The nonce is the four secret bytes of the key block plus the record's own
    epoch and sequence number, which travel in front of the ciphertext.
    """

    def __init__(self, key: bytes, implicit_iv: bytes) -> None:
        self._cipher = AESGCM(key)
        self._implicit_iv = implicit_iv

    def protect(
        self, content_type: int, epoch: int, sequence: int, plaintext: bytes
    ) -> bytes:
        """Encrypt one record fragment: explicit nonce, ciphertext and tag."""
        explicit_nonce = _explicit_nonce(epoch, sequence)
        sealed = self._cipher.encrypt(
            self._implicit_iv + explicit_nonce,
            plaintext,
            _additional_data(explicit_nonce, content_type, len(plaintext)),
        )
        return explicit_nonce + sealed

    def unprotect(self, content_type: int, fragment: bytes) -> bytes:
        """Decrypt one record fragment.

        The epoch and sequence number are read back off the fragment rather
        than trusted from the record header, because that is what the sender
        authenticated.

        Raises:
            ValueError: If the fragment is too short.
            InvalidTag: If it was not written with the matching key.
        """
        if len(fragment) < EXPLICIT_NONCE_LENGTH + TAG_LENGTH:
            raise ValueError(f"Record fragment is too short: {len(fragment)} bytes")

        explicit_nonce = fragment[:EXPLICIT_NONCE_LENGTH]
        sealed = fragment[EXPLICIT_NONCE_LENGTH:]
        plaintext_length = len(sealed) - TAG_LENGTH
        return self._cipher.decrypt(
            self._implicit_iv + explicit_nonce,
            sealed,
            _additional_data(explicit_nonce, content_type, plaintext_length),
        )


def _explicit_nonce(epoch: int, sequence: int) -> bytes:
    return struct.pack("!H", epoch) + sequence.to_bytes(6, "big")


def _additional_data(explicit_nonce: bytes, content_type: int, length: int) -> bytes:
    """Authenticated but unencrypted: the sequence number and record header."""
    return explicit_nonce + struct.pack("!BHH", content_type, DTLS_1_2, length)


def _hmac(key: bytes, message: bytes) -> bytes:
    return hmac.new(key, message, hashlib.sha256).digest()
