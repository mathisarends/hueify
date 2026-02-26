import functools
import logging
import time
from collections.abc import Callable, Coroutine
from typing import Any, ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")

type _AsyncFunc = Callable[P, Coroutine[Any, Any, R]]
type _AsyncDecorator = Callable[[_AsyncFunc], _AsyncFunc]


def timed(
    additional_text: str = "",
    min_duration_to_log: float = 0.25,
) -> _AsyncDecorator:
    def decorator(func: _AsyncFunc) -> _AsyncFunc:
        logger = logging.getLogger(func.__module__)

        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            start_time = time.perf_counter()
            result = await func(*args, **kwargs)
            execution_time = time.perf_counter() - start_time

            if execution_time > min_duration_to_log:
                function_name = additional_text.strip("-") or func.__name__
                logger.debug(f"⏳ {function_name}() took {execution_time:.2f}s")

            return result

        return wrapper

    return decorator
