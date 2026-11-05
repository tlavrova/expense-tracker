"""Read and change expenses in the database: the queries the CLI and the API use.

Each expense is one row with an id. ExpenseRow (database.py) is the table; models.py keeps plain
dataclasses, so it doesn't depend on the database, and this module converts between the two.
Nothing here reads input or prints, so the CLI and the API can both use it.

Every query takes owner, and it has no default on purpose, so no code can forget it:
  owner=LOCAL        the command-line app's own expenses (no account)
  owner=<user id>    one website account's expenses; another account's id is never matched
"""

from __future__ import annotations

from typing import Literal

from sqlalchemy import Engine, extract
from sqlmodel import col, func, select

import database
from database import ExpenseRow, StorageError
from models import Expense, ExpenseTracker, RecurringExpense

__all__ = [
    "LOCAL",
    "StorageError",
    "add",
    "delete",
    "get",
    "list_expenses",
    "load",
    "totals_by_category",
    "totals_by_month",
    "update",
]

LOCAL: None = None
"""owner for the command-line app: expenses that belong to no account."""

Owner = int | None


def _owned_by(statement, owner: Owner):
    """Only the rows of this owner (LOCAL means: the rows without an account)."""
    if owner is LOCAL:
        return statement.where(col(ExpenseRow.user_id).is_(None))
    return statement.where(ExpenseRow.user_id == owner)


def row_from_expense(expense: Expense, owner: Owner) -> ExpenseRow:
    return ExpenseRow(
        id=expense.id,
        amount=expense.amount,
        category=expense.category,
        description=expense.description,
        date=expense.date,
        frequency=getattr(expense, "frequency", None),
        user_id=owner,
    )


def expense_from_row(row: ExpenseRow) -> Expense:
    """Build an Expense, or a RecurringExpense when the row has a frequency. The model validates."""
    if row.frequency:
        return RecurringExpense(
            row.amount, row.category, row.description, row.date, row.frequency, id=row.id
        )
    return Expense(row.amount, row.category, row.description, row.date, id=row.id)


def load(*, owner: Owner, engine: Engine | None = None) -> ExpenseTracker:
    """All of the owner's expenses, in the order they were added (the CLI keeps them in memory)."""
    return ExpenseTracker(list_expenses(owner=owner, engine=engine))


def list_expenses(
    *,
    owner: Owner,
    category: str | None = None,
    year_month: tuple[int, int] | None = None,
    sort: Literal["amount", "date"] | None = None,
    engine: Engine | None = None,
) -> list[Expense]:
    """The owner's expenses, filtered and sorted by the database (WHERE / ORDER BY).

    sort: "amount" largest first, "date" oldest first, None in the order they were added.
    """
    statement = _owned_by(select(ExpenseRow), owner)
    if category:
        statement = statement.where(ExpenseRow.category == category.strip().lower())
    if year_month:
        year, month = year_month
        statement = statement.where(
            extract("year", ExpenseRow.date) == year, extract("month", ExpenseRow.date) == month
        )
    if sort == "amount":
        statement = statement.order_by(col(ExpenseRow.amount).desc(), col(ExpenseRow.id))
    elif sort == "date":
        statement = statement.order_by(col(ExpenseRow.date), col(ExpenseRow.id))
    else:
        statement = statement.order_by(col(ExpenseRow.id))
    with database.open_session("read the expenses", engine) as session:
        return [expense_from_row(row) for row in session.exec(statement)]


def add(expense: Expense, *, owner: Owner, engine: Engine | None = None) -> Expense:
    """Insert one expense for the owner and set its new id on it."""
    with database.open_session("save the expense", engine) as session:
        row = row_from_expense(expense, owner)
        session.add(row)
        session.commit()
        expense.id = row.id
    return expense


def get(expense_id: int, *, owner: Owner, engine: Engine | None = None) -> Expense | None:
    """One of the owner's expenses, or None if there is none with this id for this owner."""
    with database.open_session("read the expense", engine) as session:
        row = session.exec(_owned_by(select(ExpenseRow), owner).where(ExpenseRow.id == expense_id)).first()
        return None if row is None else expense_from_row(row)


def update(expense_id: int, expense: Expense, *, owner: Owner, engine: Engine | None = None) -> Expense | None:
    """Replace one of the owner's expenses with these values (it keeps its id and owner).

    None if there is none with this id for this owner.
    """
    with database.open_session("save the expense", engine) as session:
        row = session.exec(_owned_by(select(ExpenseRow), owner).where(ExpenseRow.id == expense_id)).first()
        if row is None:
            return None
        new = row_from_expense(expense, owner)
        for field in ("amount", "category", "description", "date", "frequency"):
            setattr(row, field, getattr(new, field))
        session.add(row)
        session.commit()
    expense.id = expense_id
    return expense


def delete(expense_id: int, *, owner: Owner, engine: Engine | None = None) -> bool:
    """Delete one of the owner's expenses. False if there is none with this id for this owner."""
    with database.open_session("delete the expense", engine) as session:
        row = session.exec(_owned_by(select(ExpenseRow), owner).where(ExpenseRow.id == expense_id)).first()
        if row is None:
            return False
        session.delete(row)
        session.commit()
    return True


def totals_by_category(*, owner: Owner, engine: Engine | None = None) -> dict[str, float]:
    """Category -> total amount, A to Z, added up by the database (GROUP BY)."""
    statement = _owned_by(
        select(ExpenseRow.category, func.sum(ExpenseRow.amount)), owner
    ).group_by(ExpenseRow.category).order_by(ExpenseRow.category)
    with database.open_session("read the totals", engine) as session:
        return {category: total for category, total in session.exec(statement)}


def totals_by_month(*, owner: Owner, engine: Engine | None = None) -> dict[str, float]:
    """"YYYY-MM" -> total amount, oldest month first, added up by the database (GROUP BY)."""
    year = extract("year", ExpenseRow.date)
    month = extract("month", ExpenseRow.date)
    statement = (
        _owned_by(select(year, month, func.sum(ExpenseRow.amount)), owner)
        .group_by(year, month)
        .order_by(year, month)
    )
    with database.open_session("read the totals", engine) as session:
        return {f"{int(y):04d}-{int(m):02d}": total for y, m, total in session.exec(statement)}
