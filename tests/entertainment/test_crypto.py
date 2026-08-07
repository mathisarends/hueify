import hashlib

import pytest

from hueify.entertainment import crypto
from hueify.entertainment.crypto import (
    RecordAuthenticationError,
    RecordProtection,
    SessionKeys,
)
from hueify.entertainment.dtls import ContentType

PSK = bytes.fromhex("0123456789abcdef0123456789abcdef")
CLIENT_RANDOM = bytes(range(32))
SERVER_RANDOM = bytes(range(32, 64))

KEY_LENGTH = 16
IMPLICIT_IV_LENGTH = 4
EXPLICIT_NONCE_LENGTH = 8
MASTER_SECRET_LENGTH = 48
VERIFY_DATA_LENGTH = 12


def test_public_api_is_explicit() -> None:
    assert crypto.__all__ == [
        "RecordAuthenticationError",
        "RecordProtection",
        "SessionKeys",
    ]


class TestPseudorandomFunction:
    def test_matches_the_published_tls_1_2_sha256_vector(self) -> None:
        """The only independent check of the key schedule there can be.

        Everything else in the handshake is derived from this function, so a
        vector from outside hueify is worth more here than any round trip.
        """
        secret = bytes.fromhex("9bbe436ba940f017b17652849a71db35")
        seed = bytes.fromhex("a0ba9f936cda311827a6f796ffd5198c")
        expected = bytes.fromhex(
            "e3f229ba727be17b8d122620557cd453c2aab21d07c3d495329b52d4e61edb5a"
            "6b301791e90d35c9c9a46b4e14baf9af0fa022f7077def17abfd3797c0564bab"
            "4fbc91666e9def9b97fce34f796789baa48082d122ee42c5a72e5a5110fff701"
            "8734"
        )

        assert crypto._prf(secret, b"test label", seed, len(expected)) == expected

    def test_stretches_to_any_length(self) -> None:
        assert len(crypto._prf(PSK, b"label", b"seed", 100)) == 100
        assert crypto._prf(PSK, b"label", b"seed", 100)[:32] == crypto._prf(
            PSK, b"label", b"seed", 32
        )

    def test_label_and_seed_both_change_the_output(self) -> None:
        assert crypto._prf(PSK, b"a", b"seed", 16) != crypto._prf(
            PSK, b"b", b"seed", 16
        )
        assert crypto._prf(PSK, b"a", b"one", 16) != crypto._prf(PSK, b"a", b"two", 16)


class TestPskPremasterSecret:
    def test_pads_the_missing_key_agreement_with_zeroes(self) -> None:
        assert crypto._psk_premaster_secret(b"\xaa\xbb") == (
            b"\x00\x02"  # length of the other half
            b"\x00\x00"  # which a pure PSK exchange does not have
            b"\x00\x02"  # length of the key
            b"\xaa\xbb"  # the key itself
        )


class TestSessionKeys:
    @pytest.fixture
    def keys(self) -> SessionKeys:
        return SessionKeys.derive(PSK, CLIENT_RANDOM, SERVER_RANDOM)

    def test_derives_one_key_and_one_iv_per_direction(self, keys: SessionKeys) -> None:
        assert len(keys._master_secret) == MASTER_SECRET_LENGTH
        assert len(keys._client_write_key) == KEY_LENGTH
        assert len(keys._server_write_key) == KEY_LENGTH
        assert keys._client_write_key != keys._server_write_key
        assert keys._client_write_iv != keys._server_write_iv

    def test_is_reproducible_from_the_same_handshake(self, keys: SessionKeys) -> None:
        assert SessionKeys.derive(PSK, CLIENT_RANDOM, SERVER_RANDOM) == keys

    def test_a_different_client_key_derives_different_keys(
        self, keys: SessionKeys
    ) -> None:
        other = SessionKeys.derive(b"\x00" * 16, CLIENT_RANDOM, SERVER_RANDOM)

        assert other._client_write_key != keys._client_write_key

    def test_the_randoms_are_not_interchangeable(self, keys: SessionKeys) -> None:
        swapped = SessionKeys.derive(PSK, SERVER_RANDOM, CLIENT_RANDOM)

        assert swapped._master_secret != keys._master_secret

    def test_each_side_proves_the_transcript_with_its_own_label(
        self, keys: SessionKeys
    ) -> None:
        client = keys.client_finished(b"transcript")
        server = keys.server_finished(b"transcript")

        assert len(client) == VERIFY_DATA_LENGTH
        assert client != server

    def test_finished_proofs_use_the_tls_labels(self, keys: SessionKeys) -> None:
        transcript = b"transcript"
        transcript_hash = hashlib.sha256(transcript).digest()

        assert keys.client_finished(transcript) == crypto._prf(
            keys._master_secret,
            b"client finished",
            transcript_hash,
            VERIFY_DATA_LENGTH,
        )
        assert keys.server_finished(transcript) == crypto._prf(
            keys._master_secret,
            b"server finished",
            transcript_hash,
            VERIFY_DATA_LENGTH,
        )

    def test_a_changed_transcript_changes_the_proof(self, keys: SessionKeys) -> None:
        assert keys.client_finished(b"a") != keys.client_finished(b"b")


class TestTheOrderTheBridgeInsistsOn:
    """The key schedule, recomputed from the PRF instead of from ``derive``.

    Every round trip in this suite has both sides call ``SessionKeys.derive``,
    so a swapped pair of randoms or a swapped pair of key halves would stay
    green here and still be rejected by a real bridge - it would decrypt
    nothing and answer ``bad_record_mac``. These assertions spell out the order
    RFC 5246 section 6.3 fixes, which is the one a bridge agrees with.
    """

    @pytest.fixture
    def keys(self) -> SessionKeys:
        return SessionKeys.derive(PSK, CLIENT_RANDOM, SERVER_RANDOM)

    @pytest.fixture
    def key_block(self, keys: SessionKeys) -> bytes:
        # Note the randoms: the master secret is seeded client first, the key
        # block server first.
        return crypto._prf(
            keys._master_secret,
            b"key expansion",
            SERVER_RANDOM + CLIENT_RANDOM,
            2 * KEY_LENGTH + 2 * IMPLICIT_IV_LENGTH,
        )

    def test_the_master_secret_comes_from_the_psk_and_both_randoms(
        self, keys: SessionKeys
    ) -> None:
        assert keys._master_secret == crypto._prf(
            crypto._psk_premaster_secret(PSK),
            b"master secret",
            CLIENT_RANDOM + SERVER_RANDOM,
            MASTER_SECRET_LENGTH,
        )

    def test_the_key_block_is_split_keys_first_then_ivs(
        self, keys: SessionKeys, key_block: bytes
    ) -> None:
        assert keys._client_write_key == key_block[:KEY_LENGTH]
        assert keys._server_write_key == key_block[KEY_LENGTH : 2 * KEY_LENGTH]
        assert keys._client_write_iv == key_block[32:36]
        assert keys._server_write_iv == key_block[36:40]

    def test_this_side_writes_with_the_first_half_of_the_block(
        self, keys: SessionKeys, key_block: bytes
    ) -> None:
        """Which half is 'ours' is the part a symmetric round trip cannot show."""
        fragment = keys.client_protection().protect(
            ContentType.APPLICATION_DATA, epoch=1, sequence=0, plaintext=b"frame"
        )

        as_the_bridge_reads_it = RecordProtection(
            key_block[:KEY_LENGTH], key_block[32:36]
        )

        assert (
            as_the_bridge_reads_it.unprotect(ContentType.APPLICATION_DATA, fragment)
            == b"frame"
        )

    def test_the_bridge_writes_with_the_second_half(
        self, keys: SessionKeys, key_block: bytes
    ) -> None:
        fragment = RecordProtection(
            key_block[KEY_LENGTH : 2 * KEY_LENGTH], key_block[36:40]
        ).protect(ContentType.HANDSHAKE, epoch=1, sequence=0, plaintext=b"finished")

        assert (
            keys.server_protection().unprotect(ContentType.HANDSHAKE, fragment)
            == b"finished"
        )


class TestRecordProtection:
    @pytest.fixture
    def keys(self) -> SessionKeys:
        return SessionKeys.derive(PSK, CLIENT_RANDOM, SERVER_RANDOM)

    def test_the_other_side_reads_back_what_was_written(
        self, keys: SessionKeys
    ) -> None:
        fragment = keys.client_protection().protect(
            ContentType.APPLICATION_DATA, epoch=1, sequence=3, plaintext=b"frame"
        )

        plaintext = RecordProtection(
            keys._client_write_key, keys._client_write_iv
        ).unprotect(ContentType.APPLICATION_DATA, fragment)

        assert plaintext == b"frame"

    def test_the_fragment_carries_its_epoch_and_sequence_in_front(
        self, keys: SessionKeys
    ) -> None:
        fragment = keys.client_protection().protect(
            ContentType.APPLICATION_DATA, epoch=1, sequence=258, plaintext=b"frame"
        )

        assert fragment[:EXPLICIT_NONCE_LENGTH] == b"\x00\x01\x00\x00\x00\x00\x01\x02"

    def test_ciphertext_and_tag_are_added_to_the_plaintext(
        self, keys: SessionKeys
    ) -> None:
        fragment = keys.client_protection().protect(
            ContentType.APPLICATION_DATA, epoch=1, sequence=0, plaintext=b"frame"
        )

        assert len(fragment) == EXPLICIT_NONCE_LENGTH + len(b"frame") + 16
        assert b"frame" not in fragment

    def test_every_record_is_encrypted_differently(self, keys: SessionKeys) -> None:
        protection = keys.client_protection()
        first = protection.protect(ContentType.APPLICATION_DATA, 1, 0, b"frame")
        second = protection.protect(ContentType.APPLICATION_DATA, 1, 1, b"frame")

        assert first != second

    def test_the_wrong_key_cannot_read_it(self, keys: SessionKeys) -> None:
        fragment = keys.client_protection().protect(
            ContentType.APPLICATION_DATA, 1, 0, b"frame"
        )

        with pytest.raises(RecordAuthenticationError):
            keys.server_protection().unprotect(ContentType.APPLICATION_DATA, fragment)

    def test_the_content_type_is_authenticated_too(self, keys: SessionKeys) -> None:
        fragment = keys.client_protection().protect(
            ContentType.HANDSHAKE, 1, 0, b"frame"
        )

        with pytest.raises(RecordAuthenticationError):
            keys.client_protection().unprotect(ContentType.APPLICATION_DATA, fragment)

    def test_a_tampered_record_does_not_decrypt(self, keys: SessionKeys) -> None:
        fragment = bytearray(
            keys.client_protection().protect(
                ContentType.APPLICATION_DATA, 1, 0, b"frame"
            )
        )
        fragment[-1] ^= 0xFF

        with pytest.raises(RecordAuthenticationError):
            keys.client_protection().unprotect(
                ContentType.APPLICATION_DATA, bytes(fragment)
            )

    def test_a_fragment_that_cannot_hold_a_record_is_refused(
        self, keys: SessionKeys
    ) -> None:
        with pytest.raises(ValueError, match="too short"):
            keys.client_protection().unprotect(ContentType.APPLICATION_DATA, b"short")
