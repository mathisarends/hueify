import pytest
from cryptography.exceptions import InvalidTag

from hueify.entertainment.crypto import (
    CLIENT_FINISHED_LABEL,
    EXPLICIT_NONCE_LENGTH,
    KEY_LENGTH,
    MASTER_SECRET_LENGTH,
    SERVER_FINISHED_LABEL,
    VERIFY_DATA_LENGTH,
    RecordProtection,
    SessionKeys,
    prf,
    psk_premaster_secret,
)
from hueify.entertainment.dtls import ContentType

PSK = bytes.fromhex("0123456789abcdef0123456789abcdef")
CLIENT_RANDOM = bytes(range(32))
SERVER_RANDOM = bytes(range(32, 64))


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

        assert prf(secret, b"test label", seed, len(expected)) == expected

    def test_stretches_to_any_length(self) -> None:
        assert len(prf(PSK, b"label", b"seed", 100)) == 100
        assert prf(PSK, b"label", b"seed", 100)[:32] == prf(PSK, b"label", b"seed", 32)

    def test_label_and_seed_both_change_the_output(self) -> None:
        assert prf(PSK, b"a", b"seed", 16) != prf(PSK, b"b", b"seed", 16)
        assert prf(PSK, b"a", b"one", 16) != prf(PSK, b"a", b"two", 16)


class TestPskPremasterSecret:
    def test_pads_the_missing_key_agreement_with_zeroes(self) -> None:
        assert psk_premaster_secret(b"\xaa\xbb") == (
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
        assert len(keys.master_secret) == MASTER_SECRET_LENGTH
        assert len(keys.client_write_key) == KEY_LENGTH
        assert len(keys.server_write_key) == KEY_LENGTH
        assert keys.client_write_key != keys.server_write_key
        assert keys.client_write_iv != keys.server_write_iv

    def test_is_reproducible_from_the_same_handshake(self, keys: SessionKeys) -> None:
        assert SessionKeys.derive(PSK, CLIENT_RANDOM, SERVER_RANDOM) == keys

    def test_a_different_client_key_derives_different_keys(
        self, keys: SessionKeys
    ) -> None:
        other = SessionKeys.derive(b"\x00" * 16, CLIENT_RANDOM, SERVER_RANDOM)

        assert other.client_write_key != keys.client_write_key

    def test_the_randoms_are_not_interchangeable(self, keys: SessionKeys) -> None:
        swapped = SessionKeys.derive(PSK, SERVER_RANDOM, CLIENT_RANDOM)

        assert swapped.master_secret != keys.master_secret

    def test_each_side_proves_the_transcript_with_its_own_label(
        self, keys: SessionKeys
    ) -> None:
        client = keys.verify_data(CLIENT_FINISHED_LABEL, b"transcript")
        server = keys.verify_data(SERVER_FINISHED_LABEL, b"transcript")

        assert len(client) == VERIFY_DATA_LENGTH
        assert client != server

    def test_a_changed_transcript_changes_the_proof(self, keys: SessionKeys) -> None:
        assert keys.verify_data(CLIENT_FINISHED_LABEL, b"a") != keys.verify_data(
            CLIENT_FINISHED_LABEL, b"b"
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
            keys.client_write_key, keys.client_write_iv
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

        with pytest.raises(InvalidTag):
            keys.server_protection().unprotect(ContentType.APPLICATION_DATA, fragment)

    def test_the_content_type_is_authenticated_too(self, keys: SessionKeys) -> None:
        fragment = keys.client_protection().protect(
            ContentType.HANDSHAKE, 1, 0, b"frame"
        )

        with pytest.raises(InvalidTag):
            keys.client_protection().unprotect(ContentType.APPLICATION_DATA, fragment)

    def test_a_tampered_record_does_not_decrypt(self, keys: SessionKeys) -> None:
        fragment = bytearray(
            keys.client_protection().protect(
                ContentType.APPLICATION_DATA, 1, 0, b"frame"
            )
        )
        fragment[-1] ^= 0xFF

        with pytest.raises(InvalidTag):
            keys.client_protection().unprotect(
                ContentType.APPLICATION_DATA, bytes(fragment)
            )

    def test_a_fragment_that_cannot_hold_a_record_is_refused(
        self, keys: SessionKeys
    ) -> None:
        with pytest.raises(ValueError, match="too short"):
            keys.client_protection().unprotect(ContentType.APPLICATION_DATA, b"short")
