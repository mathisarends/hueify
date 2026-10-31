from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass


@dataclass(slots=True)
class _Invocation:
    active: bool = True


class CallbackContext:
    """Recognize callbacks that shutdown must not wait on recursively."""

    def __init__(self) -> None:
        self._invocation: ContextVar[_Invocation | None] = ContextVar(
            "callback_invocation", default=None
        )

    @property
    def active(self) -> bool:
        invocation = self._invocation.get()
        return invocation is not None and invocation.active

    @contextmanager
    def enter(self) -> Iterator[None]:
        invocation = _Invocation()
        token = self._invocation.set(invocation)
        try:
            yield
        finally:
            # Child tasks inherit the context, but cease to be callbacks once
            # this invocation has finished (for example, background workers).
            invocation.active = False
            self._invocation.reset(token)
