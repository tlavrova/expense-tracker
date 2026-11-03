"""Decorators shared by the CLI (and later the API)."""

from __future__ import annotations

import functools
import logging
import time
from typing import Any, Callable, TypeVar

logger = logging.getLogger("expense_tracker")

F = TypeVar("F", bound=Callable[..., Any])


def log_action(func: F) -> F:
    """Log when an action starts, how long it took, and any error it raised.

    Where the log goes is decided by the program (main.py), not here.
    """

    @functools.wraps(func)  # keeps the original name and docstring
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        name = func.__name__
        logger.info("%s: started", name)
        start = time.perf_counter()
        try:
            result = func(*args, **kwargs)
        except Exception:
            logger.exception("%s: failed after %.0f ms", name, (time.perf_counter() - start) * 1000)
            raise
        logger.info("%s: finished in %.0f ms", name, (time.perf_counter() - start) * 1000)
        return result

    return wrapper  # type: ignore[return-value]
