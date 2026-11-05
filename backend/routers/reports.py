"""Reports over your expenses: the Summary page's totals, and one month against your budgets.

reports.py does the adding up, in the database.
"""

from __future__ import annotations

from fastapi import APIRouter, Query

import budgets
import reports
from routers.params import parse_month
from schemas import MonthReport, MonthRow, Summary
from security import CurrentUser

router = APIRouter(tags=["reports"])


@router.get("/summary", response_model=Summary, response_model_by_alias=True)
def summary(user: CurrentUser) -> Summary:
    """Your totals per category (added up by the database) and the overall total."""
    totals = reports.totals_by_category(owner=user.id)
    return Summary(totals_by_category=totals, total=sum(totals.values()))


@router.get("/reports/month", response_model=MonthReport, response_model_by_alias=True)
def month_report(
    user: CurrentUser, month: str = Query(description="YYYY-MM", examples=["2026-11"])
) -> MonthReport:
    """What you spent per category in one month, next to each category's budget.

    Every category that has a budget or spending that month, A to Z; budget is empty (null) for
    categories without one.
    """
    year_month = parse_month(month)
    assert year_month is not None and user.id is not None
    spent = reports.totals_by_category(owner=user.id, year_month=year_month)
    budget = budgets.list_budgets(owner=user.id)
    rows = [
        MonthRow(category=category, spent=spent.get(category, 0.0), budget=budget.get(category))
        for category in sorted(spent.keys() | budget.keys())
    ]
    return MonthReport(
        month=f"{year_month[0]:04d}-{year_month[1]:02d}",
        rows=rows,
        total_spent=sum(spent.values()),
        total_budget=sum(budget.values()),
    )
