"""Query parameters several routers read the same way."""

from __future__ import annotations

import datetime

from fastapi import HTTPException, status


def parse_month(month: str | None) -> tuple[int, int] | None:
    """"2026-11" -> (2026, 11); None stays None; anything else is a 422 with the right format."""
    if not month:
        return None
    try:
        first_day = datetime.datetime.strptime(month, "%Y-%m")
    except ValueError:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "month must be YYYY-MM, for example 2026-11."
        ) from None
    return first_day.year, first_day.month
