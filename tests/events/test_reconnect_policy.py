from hueify.sse.retry import Backoff, ReconnectPolicy


def make_backoff(**overrides: float) -> Backoff:
    policy = ReconnectPolicy(
        initial_backoff=1.0,
        max_backoff=8.0,
        backoff_factor=2.0,
        **overrides,
    )
    return Backoff(policy)


class TestBackoff:
    def test_delays_grow_exponentially(self) -> None:
        backoff = make_backoff()

        delays = [backoff.next_delay() for _ in range(4)]

        assert all(
            ceiling / 2 <= delay <= ceiling
            for delay, ceiling in zip(delays, [1.0, 2.0, 4.0, 8.0], strict=True)
        )

    def test_delays_never_exceed_the_ceiling(self) -> None:
        backoff = make_backoff()

        delays = [backoff.next_delay() for _ in range(10)]

        assert max(delays) <= 8.0

    def test_delays_are_never_zero(self) -> None:
        backoff = make_backoff()

        delays = [backoff.next_delay() for _ in range(10)]

        assert min(delays) >= 0.5

    def test_delays_are_jittered(self) -> None:
        delays = {make_backoff().next_delay() for _ in range(20)}

        assert len(delays) > 1

    def test_reset_starts_over_at_the_shortest_delay(self) -> None:
        backoff = make_backoff()
        for _ in range(5):
            backoff.next_delay()

        backoff.reset()

        assert backoff.next_delay() <= 1.0
