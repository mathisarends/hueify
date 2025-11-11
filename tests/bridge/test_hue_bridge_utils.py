from hueify.bridge.utils import is_valid_ip, is_valid_user_id
import pytest


def test_is_valid_ip_valid_addresses():
    assert is_valid_ip("192.168.1.1")
    assert is_valid_ip("0.0.0.0")
    assert is_valid_ip("255.255.255.255")
    assert is_valid_ip("10.0.0.1")
    assert is_valid_ip("127.0.0.1")


def test_is_valid_ip_invalid_range():
    """Test IP addresses with values out of range."""
    assert not is_valid_ip("256.1.1.1")
    assert not is_valid_ip("1.256.1.1")
    assert not is_valid_ip("1.1.256.1")
    assert not is_valid_ip("1.1.1.256")
    assert not is_valid_ip("999.999.999.999")
    assert not is_valid_ip("-1.0.0.0")


def test_is_valid_ip_invalid_format():
    """Test IP addresses with invalid format."""
    assert not is_valid_ip("192.168.1")  # too few parts
    assert not is_valid_ip("192.168.1.1.1")  # too many parts
    assert not is_valid_ip("192.168.1.a")  # non-numeric
    assert not is_valid_ip("192.168..1")  # empty part
    assert not is_valid_ip("")  # empty string
    assert not is_valid_ip("...")  # only dots
    assert not is_valid_ip("192.168.1.1.")  # trailing dot


def test_is_valid_ip_edge_cases():
    """Test edge cases for IP validation."""
    assert not is_valid_ip("192.168.1.1.extra")
    assert not is_valid_ip(" 192.168.1.1")  # leading space
    assert not is_valid_ip("192.168.1.1 ")  # trailing space
    assert not is_valid_ip("192 168 1 1")  # spaces instead of dots


@pytest.mark.parametrize("ip,expected", [
    ("192.168.1.1", True),
    ("0.0.0.0", True),
    ("255.255.255.255", True),
    ("256.1.1.1", False),
    ("192.168.1", False),
    ("192.168.1.1.1", False),
    ("a.b.c.d", False),
])
def test_is_valid_ip_parametrized(ip, expected):
    """Parametrized test for IP validation."""
    assert is_valid_ip(ip) == expected


def test_is_valid_user_id_valid():
    assert is_valid_user_id("a" * 20)  # exactly 20 chars
    assert is_valid_user_id("a" * 50)  # more than 20 chars
    assert is_valid_user_id("abc123def456ghi789jk")  # alphanumeric mix
    assert is_valid_user_id("12345678901234567890")  # only numbers


def test_is_valid_user_id_too_short():
    """Test user IDs that are too short."""
    assert not is_valid_user_id("a" * 19)  # 19 chars
    assert not is_valid_user_id("abc123")  # 6 chars
    assert not is_valid_user_id("")  # empty


def test_is_valid_user_id_invalid_characters():
    """Test user IDs with invalid characters."""
    assert not is_valid_user_id("a" * 19 + "_")  # underscore
    assert not is_valid_user_id("a" * 19 + "-")  # hyphen
    assert not is_valid_user_id("a" * 19 + " ")  # space
    assert not is_valid_user_id("abc123def456ghi789j!")  # special char
    assert not is_valid_user_id("user@example.com1234")  # email-like


@pytest.mark.parametrize("user_id,expected", [
    ("a" * 20, True),
    ("abc123def456ghi789jk", True),
    ("12345678901234567890", True),
    ("a" * 19, False),
    ("abc123", False),
    ("", False),
    ("abc123def456_ghi789jk", False),
    ("abc123-def456-ghi789", False),
])
def test_is_valid_user_id_parametrized(user_id, expected):
    """Parametrized test for user ID validation."""
    assert is_valid_user_id(user_id) == expected