"""Reports over your expenses: the totals for the Summary page (reports.py does the adding up)."""

from __future__ import annotations

from fastapi import APIRouter

import reports
from schemas import Summary
from security import CurrentUser

router = APIRouter(tags=["reports"])


@router.get("/summary", response_model=Summary, response_model_by_alias=True)
def summary(user: CurrentUser) -> Summary:
    """Your totals per category (added up by the database) and the overall total."""
    totals = reports.totals_by_category(owner=user.id)
    return Summary(totals_by_category=totals, total=sum(totals.values()))
