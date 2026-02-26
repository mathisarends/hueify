import asyncio
import logging

import pytest

from hueify.shared.decorators import timed


class TestTimedDecorator:
    @pytest.mark.asyncio
    async def test_returns_function_result(self) -> None:
        @timed()
        async def fetch() -> str:
            return "ok"

        result = await fetch()
        assert result == "ok"

    @pytest.mark.asyncio
    async def test_passes_arguments_to_wrapped_function(self) -> None:
        @timed()
        async def add(a: int, b: int) -> int:
            return a + b

        result = await add(2, 3)
        assert result == 5

    @pytest.mark.asyncio
    async def test_logs_when_duration_exceeds_threshold(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        @timed(min_duration_to_log=0.0)
        async def slow() -> None:
            await asyncio.sleep(0.01)

        with caplog.at_level(logging.DEBUG):
            await slow()

        assert any("slow" in record.message for record in caplog.records)

    @pytest.mark.asyncio
    async def test_does_not_log_when_duration_below_threshold(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        @timed(min_duration_to_log=999.0)
        async def fast() -> None:
            pass

        with caplog.at_level(logging.DEBUG):
            await fast()

        assert not caplog.records

    @pytest.mark.asyncio
    async def test_uses_additional_text_in_log_message(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        @timed(additional_text="my-label", min_duration_to_log=0.0)
        async def op() -> None:
            await asyncio.sleep(0.01)

        with caplog.at_level(logging.DEBUG):
            await op()

        assert any("my-label" in record.message for record in caplog.records)

    @pytest.mark.asyncio
    async def test_falls_back_to_function_name_when_no_additional_text(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        @timed(min_duration_to_log=0.0)
        async def my_operation() -> None:
            await asyncio.sleep(0.01)

        with caplog.at_level(logging.DEBUG):
            await my_operation()

        assert any("my_operation" in record.message for record in caplog.records)

    @pytest.mark.asyncio
    async def test_preserves_function_metadata(self) -> None:
        @timed()
        async def documented() -> None:
            pass

        assert documented.__name__ == "documented"

    @pytest.mark.asyncio
    async def test_propagates_exceptions(self) -> None:
        @timed()
        async def failing() -> None:
            raise ValueError("boom")

        with pytest.raises(ValueError, match="boom"):
            await failing()
