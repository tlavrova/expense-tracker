"""Store expenses in a database through SQLModel.

Which database comes from the DATABASE_URL environment variable:
  not set                          SQLite file expenses.db next to this file (on your Mac)
  postgresql://user:pass@host/db   Postgres (online, stage 13; needs a Postgres driver then)

Each expense is one row with an id. ExpenseRow is the table; models.py keeps plain dataclasses,
so it doesn't depend on the database, and this module converts between the two.
Nothing here reads input or prints, so the API (stage 9) can reuse it.
"""

from __future__ import annotations

import functools
import json
import os
from contextlib import contextmanager
from datetime import date as Date
from pathlib import Path
from typing import Iterator

from sqlalchemy import Engine, extract
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Field, Session, SQLModel, create_engine, func, select

from models import Expense, ExpenseTracker, RecurringExpense

DEFAULT_DB_PATH = Path(__file__).parent / "expenses.db"
JSON_PATH = Path(__file__).parent / "expenses.json"  # the file used before stage 8a


class StorageError(Exception):
    """Raised when the database can't be read or written, or holds invalid data."""


class ExpenseRow(SQLModel, table=True):
    """One expense in the "expenses" table. frequency is empty for one-off expenses."""

    __tablename__ = "expenses"

    id: int | None = Field(default=None, primary_key=True)
    amount: float
    category: str = Field(index=True)
    description: str
    date: Date = Field(index=True)
    frequency: str | None = None


def database_url() -> str:
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        return f"sqlite:///{DEFAULT_DB_PATH}"
    # Some hosts hand out "postgres://", which SQLAlchemy doesn't accept.
    if url.startswith("postgres://"):
        url = "postgresql://" + url.removeprefix("postgres://")
    return url


@functools.lru_cache(maxsize=1)
def get_engine(url: str | None = None) -> Engine:
    """Connect to the database (once) and create the table if it isn't there yet."""
    url = url or database_url()
    # SQLite allows one thread per connection by default; the API (stage 9) uses several.
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    try:
        engine = create_engine(url, connect_args=connect_args)
        SQLModel.metadata.create_all(engine)
    except SQLAlchemyError as error:
        raise StorageError(f"Can't open the database: {_short(error)}") from error
    return engine


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


@contextmanager
def _session(action: str, engine: Engine | None = None) -> Iterator[Session]:
    """A database session; any database error becomes StorageError("Can't <action>: ...").

    ValueError counts too: it means a row holds data the models reject.
    """
    try:
        with Session(engine or get_engine()) as session:
            yield session
    except (SQLAlchemyError, ValueError) as error:
        raise StorageError(f"Can't {action}: {_short(error)}") from error


def _short(error: Exception) -> str:
    """First line only: SQLAlchemy adds the SQL and its values below it (the log keeps it all)."""
    return str(error).splitlines()[0]


def load(engine: Engine | None = None) -> ExpenseTracker:
    """All expenses, in the order they were added."""
    with _session("read the expenses", engine) as session:
        rows = session.exec(select(ExpenseRow).order_by(ExpenseRow.id)).all()
        return ExpenseTracker([expense_from_row(row) for row in rows])


def add(expense: Expense, engine: Engine | None = None) -> Expense:
    """Insert one expense and set its new id on it."""
    with _session("save the expense", engine) as session:
        row = row_from_expense(expense)
        session.add(row)
        session.commit()
        expense.id = row.id
    return expense


def delete(expense_id: int, engine: Engine | None = None) -> bool:
    """Delete one expense by id. Returns False if there was no such expense."""
    with _session("delete the expense", engine) as session:
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
    with _session("read the totals", engine) as session:
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
    with _session("read the totals", engine) as session:
        return {f"{int(y):04d}-{int(m):02d}": total for y, m, total in session.exec(statement)}


def import_json(path: Path = JSON_PATH, engine: Engine | None = None) -> int:
    """Move the expenses from the old expenses.json into the database, once.

    All rows go in in one transaction, then the file is renamed to expenses.json.imported so the
    next start doesn't import it again. Returns how many expenses were imported (0: no file).
    """
    if not path.exists():
        return 0
    try:
        with path.open(encoding="utf-8") as file:
            items = json.load(file)
        expenses = [
            RecurringExpense(**item) if "frequency" in item else Expense(**item) for item in items
        ]
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as error:
        raise StorageError(f"Can't read {path}: {error}") from error

    with _session(f"import {path}", engine) as session:
        session.add_all(row_from_expense(expense) for expense in expenses)
        session.commit()
    path.rename(path.with_name(path.name + ".imported"))
    return len(expenses)
