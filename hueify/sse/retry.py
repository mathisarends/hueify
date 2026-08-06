import random
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ReconnectPolicy:
    """Timing rules the event stream follows while recovering a lost connection."""

    initial_backoff: float = 1.0
    max_backoff: float = 30.0
    backoff_factor: float = 2.0

    # A connection that held this long did work, so the next failure is treated
    # as a new incident rather than a continuation of the previous one.
    healthy_after: float = 30.0

    connect_timeout: float = 10.0

    # The bridge stays silent while nothing changes, so this is not a health
    # signal - it is the upper bound on how long a dead socket can look alive.
    read_timeout: float = 90.0


class Backoff:
    """Exponentially growing delays, jittered so parallel clients do not sync up."""

    def __init__(self, policy: ReconnectPolicy) -> None:
        self._policy = policy
        self._attempt = 0

    def reset(self) -> None:
        self._attempt = 0

    def next_delay(self) -> float:
        ceiling = min(
            self._policy.initial_backoff * self._policy.backoff_factor**self._attempt,
            self._policy.max_backoff,
        )
        # Stop climbing once the ceiling is saturated - further increments would
        # not change the result but would eventually overflow the float power.
        if ceiling < self._policy.max_backoff:
            self._attempt += 1
        return ceiling / 2 + random.uniform(0, ceiling / 2)
