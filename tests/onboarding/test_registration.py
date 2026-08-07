from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from hueify.onboarding.registration import register_app_key


def response_with(payload: list) -> MagicMock:
    response = MagicMock()
    response.json.return_value = payload
    return response


@pytest.mark.asyncio
async def test_register_app_key_succeeds_once_the_link_button_was_pressed() -> None:
    success = response_with(
        [{"success": {"username": "abc123", "clientkey": "A" * 32}}]
    )
    with (
        patch("asyncio.sleep", new_callable=AsyncMock) as sleep,
        patch(
            "httpx.AsyncClient.post", new_callable=AsyncMock, return_value=success
        ) as post,
    ):
        app = await register_app_key("192.168.1.50")

    assert app.app_key == "abc123"
    assert app.client_key == "A" * 32
    sleep.assert_not_awaited()
    assert post.await_args.args[0] == "https://192.168.1.50/api"
    assert post.await_args.kwargs["json"] == {
        "devicetype": "hueify#setup",
        "generateclientkey": True,
    }


@pytest.mark.asyncio
async def test_register_app_key_polls_until_the_link_button_is_pressed() -> None:
    not_pressed = response_with([{"error": {"description": "link button not pressed"}}])
    success = response_with([{"success": {"username": "def456"}}])
    with (
        patch("asyncio.sleep", new_callable=AsyncMock),
        patch(
            "httpx.AsyncClient.post",
            new_callable=AsyncMock,
            side_effect=[not_pressed, not_pressed, success],
        ) as post,
    ):
        app = await register_app_key("192.168.1.50")

    assert app.app_key == "def456"
    assert post.await_count == 3


@pytest.mark.asyncio
async def test_register_app_key_tolerates_a_bridge_without_a_client_key() -> None:
    success = response_with([{"success": {"username": "abc123"}}])
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=success):
        app = await register_app_key("192.168.1.50")

    assert app.client_key is None


@pytest.mark.asyncio
async def test_register_app_key_times_out_after_the_link_button_is_never_pressed() -> (
    None
):
    not_pressed = response_with([{"error": {"description": "link button not pressed"}}])
    with (
        patch("asyncio.sleep", new_callable=AsyncMock),
        patch(
            "httpx.AsyncClient.post", new_callable=AsyncMock, return_value=not_pressed
        ),
        pytest.raises(TimeoutError, match="Link button was not pressed"),
    ):
        await register_app_key("192.168.1.50")


@pytest.mark.asyncio
async def test_register_app_key_uses_a_custom_device_type() -> None:
    success = response_with([{"success": {"username": "abc123"}}])
    with patch(
        "httpx.AsyncClient.post", new_callable=AsyncMock, return_value=success
    ) as post:
        await register_app_key("192.168.1.50", device_type="my-app#laptop")

    assert post.await_args.kwargs["json"]["devicetype"] == "my-app#laptop"
