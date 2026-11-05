"""The sliding-window counter behind the login limits, with a fake clock instead of waiting."""

import pytest

from rate_limit import RateLimit, TooManyAttempts


class Clock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def test_allows_up_to_the_limit_then_says_how_long_to_wait():
    clock = Clock()
    limit = RateLimit(limit=2, window=60, clock=clock)
    limit.check("a")
    limit.hit("a")
    clock.now += 10
    limit.check("a")
    limit.hit("a")
    with pytest.raises(TooManyAttempts) as error:
        limit.check("a")
    assert error.value.retry_after == 50  # the first hit leaves the window in 50 seconds


def test_old_hits_leave_the_window():
    clock = Clock()
    limit = RateLimit(limit=1, window=60, clock=clock)
    limit.hit("a")
    clock.now += 60
    limit.check("a")  # no error


def test_keys_are_counted_separately_and_can_be_reset():
    limit = RateLimit(limit=1, window=60, clock=Clock())
    limit.hit("a")
    limit.check("b")
    limit.reset("a")
    limit.check("a")
