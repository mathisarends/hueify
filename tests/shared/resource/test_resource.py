from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from hueify.shared.resource import Resource
from hueify.shared.resource.models import (
    ColorTemperatureState,
    DimmingState,
    LightOnState,
)


def make_light_info(
    id: UUID | None = None,
    on: bool = True,
    brightness: float = 50.0,
    mirek: int | None = 300,
) -> MagicMock:
    info = MagicMock()
    info.id = id or uuid4()
    info.on = LightOnState(on=on)
    info.dimming = DimmingState(brightness=brightness)
    info.color_temperature = ColorTemperatureState(mirek=mirek) if mirek else None
    return info


class ConcreteResource(Resource):
    def _get_resource_endpoint(self) -> str:
        return "/api/lights"


def make_resource(
    on: bool = True,
    brightness: float = 50.0,
    mirek: int | None = 300,
    cache=None,
) -> tuple[ConcreteResource, AsyncMock]:
    client = AsyncMock()
    light_info = make_light_info(on=on, brightness=brightness, mirek=mirek)
    resource = ConcreteResource(light_info=light_info, client=client, cache=cache)
    return resource, client


class TestProperties:
    def test_is_on_returns_true_when_light_is_on(self) -> None:
        resource, _ = make_resource(on=True)
        assert resource.is_on is True

    def test_is_on_returns_false_when_light_is_off(self) -> None:
        resource, _ = make_resource(on=False)
        assert resource.is_on is False

    def test_brightness_percentage_returns_current_brightness(self) -> None:
        resource, _ = make_resource(brightness=75.0)
        assert resource.brightness_percentage == 75.0

    def test_brightness_percentage_returns_zero_when_no_dimming(self) -> None:
        resource, _ = make_resource()
        resource._fallback_info.dimming = None
        assert resource.brightness_percentage == 0.0

    def test_color_temperature_percentage_converts_mirek_to_percentage(self) -> None:
        resource, _ = make_resource(mirek=153)
        assert resource.color_temperature_percentage == 0

    def test_color_temperature_percentage_returns_100_at_max_mirek(self) -> None:
        resource, _ = make_resource(mirek=500)
        assert resource.color_temperature_percentage == 100

    def test_color_temperature_percentage_returns_none_without_color_temperature(
        self,
    ) -> None:
        resource, _ = make_resource(mirek=None)
        assert resource.color_temperature_percentage is None

    def test_id_returns_light_info_id(self) -> None:
        light_id = uuid4()
        client = AsyncMock()
        info = make_light_info(id=light_id)
        resource = ConcreteResource(light_info=info, client=client)
        assert resource.id == light_id


class TestCacheLookup:
    def test_uses_cache_when_available(self) -> None:
        cache = MagicMock()
        cached_info = make_light_info(on=False)
        cache.get_by_id.return_value = cached_info

        resource, _ = make_resource(on=True, cache=cache)

        assert resource.is_on is False

    def test_falls_back_to_original_info_when_cache_miss(self) -> None:
        cache = MagicMock()
        cache.get_by_id.return_value = None

        resource, _ = make_resource(on=True, cache=cache)

        assert resource.is_on is True


class TestTurnOn:
    @pytest.mark.asyncio
    async def test_turns_on_when_light_is_off(self) -> None:
        resource, client = make_resource(on=False)
        result = await resource.turn_on()
        client.put.assert_called_once()
        assert "Turned on" in result.message

    @pytest.mark.asyncio
    async def test_skips_request_when_already_on(self) -> None:
        resource, client = make_resource(on=True)
        result = await resource.turn_on()
        client.put.assert_not_called()
        assert "Already on" in result.message


class TestTurnOff:
    @pytest.mark.asyncio
    async def test_turns_off_when_light_is_on(self) -> None:
        resource, client = make_resource(on=True)
        result = await resource.turn_off()
        client.put.assert_called_once()
        assert "Turned off" in result.message

    @pytest.mark.asyncio
    async def test_skips_request_when_already_off(self) -> None:
        resource, client = make_resource(on=False)
        result = await resource.turn_off()
        client.put.assert_not_called()
        assert "Already off" in result.message


class TestSetBrightness:
    @pytest.mark.asyncio
    async def test_sets_brightness_within_range(self) -> None:
        resource, client = make_resource()
        result = await resource.set_brightness(80)
        client.put.assert_called_once()
        assert result.final_value == 80
        assert result.clamped is False

    @pytest.mark.asyncio
    async def test_clamps_brightness_above_max(self) -> None:
        resource, _ = make_resource()
        result = await resource.set_brightness(150)
        assert result.final_value == 100
        assert result.clamped is True

    @pytest.mark.asyncio
    async def test_clamps_brightness_below_min(self) -> None:
        resource, _ = make_resource()
        result = await resource.set_brightness(-10)
        assert result.final_value == 0
        assert result.clamped is True

    @pytest.mark.asyncio
    async def test_normalizes_float_fraction_to_percentage(self) -> None:
        resource, _ = make_resource()
        result = await resource.set_brightness(0.5)
        assert result.final_value == 50


class TestIncreaseBrightness:
    @pytest.mark.asyncio
    async def test_increases_brightness_by_given_amount(self) -> None:
        resource, _ = make_resource(brightness=40.0)
        result = await resource.increase_brightness(20)
        assert result.final_value == 60
        assert result.clamped is False

    @pytest.mark.asyncio
    async def test_clamps_increase_at_maximum(self) -> None:
        resource, _ = make_resource(brightness=90.0)
        result = await resource.increase_brightness(20)
        assert result.final_value == 100
        assert result.clamped is True


class TestDecreaseBrightness:
    @pytest.mark.asyncio
    async def test_decreases_brightness_by_given_amount(self) -> None:
        resource, _ = make_resource(brightness=60.0)
        result = await resource.decrease_brightness(20)
        assert result.final_value == 40
        assert result.clamped is False

    @pytest.mark.asyncio
    async def test_clamps_decrease_at_minimum(self) -> None:
        resource, _ = make_resource(brightness=10.0)
        result = await resource.decrease_brightness(20)
        assert result.final_value == 0
        assert result.clamped is True


class TestSetColorTemperature:
    @pytest.mark.asyncio
    async def test_sets_temperature_within_range(self) -> None:
        resource, client = make_resource()
        result = await resource.set_color_temperature(50)
        client.put.assert_called_once()
        assert result.final_value == 50
        assert result.clamped is False

    @pytest.mark.asyncio
    async def test_clamps_temperature_above_max(self) -> None:
        resource, _ = make_resource()
        result = await resource.set_color_temperature(120)
        assert result.final_value == 100
        assert result.clamped is True

    @pytest.mark.asyncio
    async def test_clamps_temperature_below_min(self) -> None:
        resource, _ = make_resource()
        result = await resource.set_color_temperature(-5)
        assert result.final_value == 0
        assert result.clamped is True

    @pytest.mark.asyncio
    async def test_sends_correct_mirek_for_zero_percent(self) -> None:
        resource, client = make_resource()
        await resource.set_color_temperature(0)
        state = client.put.call_args.kwargs["data"]
        assert state.color_temperature.mirek == 153

    @pytest.mark.asyncio
    async def test_sends_correct_mirek_for_100_percent(self) -> None:
        resource, client = make_resource()
        await resource.set_color_temperature(100)
        state = client.put.call_args.kwargs["data"]
        assert state.color_temperature.mirek == 500
