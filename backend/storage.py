"""Read and change expenses in the database: the queries the CLI and the API use.

Each expense is one row with an id. ExpenseRow (database.py) is the table; models.py keeps plain
dataclasses, so it doesn't depend on the database, and this module converts between the two.
Nothing here reads input or prints, so the CLI and the API can both use it.
"""

from __future__ import annotations

from sqlalchemy import Engine, extract
from sqlmodel import func, select

import database
from database import ExpenseRow, StorageError
from models import Expense, ExpenseTracker, RecurringExpense

__all__ = ["StorageError", "add", "delete", "load", "totals_by_category", "totals_by_month"]


def row_from_expense(expense: Expense) -> ExpenseRow:
    return ExpenseRow(
        id=expense.id,
        amount=expense.amount,
        category=expense.category,
        description=expense.description,
        date=expense.date,
        frequency=getattr(expense, "frequency", None),
    )


def expense_from_row(row: ExpenseRow) -> Expense:
    """Build an Expense, or a RecurringExpense when the row has a frequency. The model validates."""
    if row.frequency:
        return RecurringExpense(
            row.amount, row.category, row.description, row.date, row.frequency, id=row.id
        )
    return Expense(row.amount, row.category, row.description, row.date, id=row.id)


def load(engine: Engine | None = None) -> ExpenseTracker:
    """All expenses, in the order they were added."""
    with database.open_session("read the expenses", engine) as session:
        rows = session.exec(select(ExpenseRow).order_by(ExpenseRow.id)).all()
        return ExpenseTracker([expense_from_row(row) for row in rows])


def add(expense: Expense, engine: Engine | None = None) -> Expense:
    """Insert one expense and set its new id on it."""
    with database.open_session("save the expense", engine) as session:
        row = row_from_expense(expense)
        session.add(row)
        session.commit()
        expense.id = row.id
    return expense


def delete(expense_id: int, engine: Engine | None = None) -> bool:
    """Delete one expense by id. Returns False if there was no such expense."""
    with database.open_session("delete the expense", engine) as session:
        row = session.get(ExpenseRow, expense_id)
        if row is None:
            return False
        session.delete(row)
        session.commit()
    return True


def totals_by_category(engine: Engine | None = None) -> dict[str, float]:
    """Category -> total amount, A to Z, added up by the database (GROUP BY)."""
    statement = (
        select(ExpenseRow.category, func.sum(ExpenseRow.amount))
        .group_by(ExpenseRow.category)
        .order_by(ExpenseRow.category)
    )
    with database.open_session("read the totals", engine) as session:
        return {category: total for category, total in session.exec(statement)}


def totals_by_month(engine: Engine | None = None) -> dict[str, float]:
    """"YYYY-MM" -> total amount, oldest month first, added up by the database (GROUP BY)."""
    year = extract("year", ExpenseRow.date)
    month = extract("month", ExpenseRow.date)
    statement = (
        select(year, month, func.sum(ExpenseRow.amount))
        .group_by(year, month)
        .order_by(year, month)
    )
    with database.open_session("read the totals", engine) as session:
        return {f"{int(y):04d}-{int(m):02d}": total for y, m, total in session.exec(statement)}
