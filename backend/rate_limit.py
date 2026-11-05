"""Limit how often something may happen in a time window, for example failed logins.

Kept in memory: it resets when the API restarts, and each API process counts on its own. That is
enough for one small server; a site with several servers would keep the counts in a shared store
such as Redis instead.
"""

from __future__ import annotations

import math
import threading
import time
from collections import deque
from typing import Callable, Hashable


class TooManyAttempts(Exception):
    """The limit is reached; retry_after is how many seconds until the next attempt is allowed."""

    def __init__(self, retry_after: int) -> None:
        super().__init__(f"Too many attempts; retry after {retry_after} s.")
        self.retry_after = retry_after


class RateLimit:
    """At most `limit` hits per key within `window` seconds (a sliding window)."""

    def __init__(self, limit: int, window: float, clock: Callable[[], float] = time.monotonic) -> None:
        self.limit = limit
        self.window = window
        self._clock = clock  # tests pass a fake clock instead of waiting
        self._hits: dict[Hashable, deque[float]] = {}
        self._lock = threading.Lock()  # FastAPI runs these endpoints in several threads

    def check(self, key: Hashable) -> None:
        """Raise TooManyAttempts if this key has used up its hits in the current window."""
        with self._lock:
            hits = self._recent(key)
            if len(hits) >= self.limit:
                retry_after = hits[0] + self.window - self._clock()
                raise TooManyAttempts(max(1, math.ceil(retry_after)))

    def hit(self, key: Hashable) -> None:
        """Count one hit for this key."""
        with self._lock:
            self._recent(key).append(self._clock())
            if len(self._hits) > 10_000:  # many different keys: forget the ones with no recent hits
                for old in [k for k in self._hits if not self._recent(k)]:
                    del self._hits[old]

    def reset(self, key: Hashable | None = None) -> None:
        """Forget one key's hits (for example after a successful login), or all of them."""
        with self._lock:
            if key is None:
                self._hits.clear()
            else:
                self._hits.pop(key, None)

    def _recent(self, key: Hashable) -> deque[float]:
        """This key's hits within the window, dropping older ones. Call with the lock held."""
        hits = self._hits.setdefault(key, deque())
        while hits and hits[0] <= self._clock() - self.window:
            hits.popleft()
        return hits
