from hueify.bridge.utils import is_valid_ip, is_valid_user_id
import pytest


def test_is_valid_ip_valid_addresses():
    assert is_valid_ip("192.168.1.1")
    assert is_valid_ip("0.0.0.0")
    assert is_valid_ip("255.255.255.255")
    assert is_valid_ip("10.0.0.1")
    assert is_valid_ip("127.0.0.1")


def test_is_valid_ip_invalid():
    assert not is_valid_ip("256.1.1.1")
    assert not is_valid_ip("1.256.1.1")
    assert not is_valid_ip("1.1.256.1")
    assert not is_valid_ip("1.1.1.256")
    assert not is_valid_ip("192.168.1")
    assert not is_valid_ip("192.168.1.1.1")
    assert not is_valid_ip("192.168.1.a")
    assert not is_valid_ip("")
    assert not is_valid_ip("192.168.1.1.extra")
    assert not is_valid_ip(" 192.168.1.1")
    assert not is_valid_ip("192.168.1.1 ")
    assert not is_valid_ip("192 168 1 1")


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
    assert is_valid_ip(ip) == expected


def test_is_valid_user_id_valid():
    assert is_valid_user_id("a" * 20)
    assert is_valid_user_id("a" * 50)
    assert is_valid_user_id("abc123def456ghi789jk")
    assert is_valid_user_id("12345678901234567890")


def test_is_valid_user_id_invalid():
    assert not is_valid_user_id("a" * 19)
    assert not is_valid_user_id("abc123")
    assert not is_valid_user_id("")
    assert not is_valid_user_id("a" * 19 + "_")
    assert not is_valid_user_id("a" * 19 + "-")
    assert not is_valid_user_id("a" * 19 + " ")
    assert not is_valid_user_id("abc123def456ghi789j!")
    assert not is_valid_user_id("user@example.com1234")


@pytest.mark.parametrize("user_id,expected", [
    ("a" * 20, True),
    ("abc123def456ghi789jk", True),
    ("12345678901234567890", True),
    ("a" * 19, False),
    ("abc123", False),
    ("", False),
    ("abc123def456_ghi789jk", False),
])
def test_is_valid_user_id_parametrized(user_id, expected):
    assert is_valid_user_id(user_id) == expected