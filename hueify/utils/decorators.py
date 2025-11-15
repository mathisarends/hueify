import functools
import logging
import time
from collections.abc import Callable, Coroutine
from typing import Any, ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")
T = TypeVar("T")

type _SyncFunc = Callable[P, R]
type _AsyncFunc = Callable[P, Coroutine[Any, Any, R]]
type _SyncDecorator = Callable[[_SyncFunc], _SyncFunc]
type _AsyncDecorator = Callable[[_AsyncFunc], _AsyncFunc]


def singleton(cls):
    original_new = cls.__new__
    instance = None

    def new_new(cls_inner, *args, **kwargs):
        nonlocal instance
        if instance is None:
            if original_new is object.__new__:
                instance = original_new(cls_inner)
            else:
                instance = original_new(cls_inner, *args, **kwargs)
        return instance

    cls.__new__ = staticmethod(new_new)
    return cls


def time_execution_sync(
    additional_text: str = "", min_duration_to_log: float = 0.25
) -> _SyncDecorator:
    def decorator(func: _SyncFunc) -> _SyncFunc:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            start_time = time.perf_counter()
            result = func(*args, **kwargs)
            execution_time = time.perf_counter() - start_time

            if execution_time > min_duration_to_log:
                logger = _get_logger_from_context(args, func)
                function_name = additional_text.strip("-") or func.__name__
                logger.debug(f"⏳ {function_name}() took {execution_time:.2f}s")

            return result

        return wrapper

    return decorator


def time_execution_async(
    additional_text: str = "",
    min_duration_to_log: float = 0.1,
) -> _AsyncDecorator:
    def decorator(func: _AsyncFunc) -> _AsyncFunc:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            start_time = time.perf_counter()
            result = await func(*args, **kwargs)
            execution_time = time.perf_counter() - start_time

            print(f"execution_time: for {func.__name__}", execution_time)

            if execution_time > min_duration_to_log:
                logger = _get_logger_from_context(args, func)
                function_name = additional_text.strip("-") or func.__name__
                logger.debug(f"⏳ {function_name}() took {execution_time:.2f}s")

            return result

        return wrapper

    return decorator


def _get_logger_from_context(args: tuple, func: Callable) -> logging.Logger:
    if _has_instance_logger(args):
        return _extract_instance_logger(args)

    return _get_module_logger(func)


def _has_instance_logger(args: tuple) -> bool:
    return bool(args) and hasattr(args[0], "logger")


def _extract_instance_logger(args: tuple) -> logging.Logger:
    return args[0].logger


def _get_module_logger(func: Callable) -> logging.Logger:
    return logging.getLogger(func.__module__)
