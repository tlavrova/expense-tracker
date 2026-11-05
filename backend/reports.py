"""Totals over one owner's expenses, added up by the database (GROUP BY): the CLI's summary and
statistics, and the website's Summary page.

The owner rule is the same as in storage.py (owner=storage.LOCAL for the CLI, or a user id).
"""

from __future__ import annotations

from sqlalchemy import Engine, extract
from sqlmodel import func, select

import database
from database import ExpenseRow
from storage import Owner, owned_by


def totals_by_category(*, owner: Owner, engine: Engine | None = None) -> dict[str, float]:
    """Category -> total amount, A to Z, added up by the database (GROUP BY)."""
    statement = owned_by(
        select(ExpenseRow.category, func.sum(ExpenseRow.amount)), owner
    ).group_by(ExpenseRow.category).order_by(ExpenseRow.category)
    with database.open_session("read the totals", engine) as session:
        return {category: total for category, total in session.exec(statement)}


def totals_by_month(*, owner: Owner, engine: Engine | None = None) -> dict[str, float]:
    """"YYYY-MM" -> total amount, oldest month first, added up by the database (GROUP BY)."""
    year = extract("year", ExpenseRow.date)
    month = extract("month", ExpenseRow.date)
    statement = (
        owned_by(select(year, month, func.sum(ExpenseRow.amount)), owner)
        .group_by(year, month)
        .order_by(year, month)
    )
    with database.open_session("read the totals", engine) as session:
        return {f"{int(y):04d}-{int(m):02d}": total for y, m, total in session.exec(statement)}
