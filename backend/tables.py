"""The database tables as SQLModel classes: what the database holds.

They must match the migrations (migrations/versions/): after changing a class here, draft the next
migration with  alembic revision --autogenerate -m "what changed"  (tests/test_database.py checks
that they match).
"""

from __future__ import annotations

from datetime import date as Date
from datetime import datetime, timezone

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


class UserRow(SQLModel, table=True):
    """One account in the "users" table. Only a hash of the password is stored, never the password."""

    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)  # stored lowercase
    password_hash: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ExpenseRow(SQLModel, table=True):
    """One expense in the "expenses" table. frequency is empty for one-off expenses.

    user_id is the account it belongs to (website); empty for the command-line app's own expenses.
    """

    __tablename__ = "expenses"

    id: int | None = Field(default=None, primary_key=True)
    amount: float
    category: str = Field(index=True)
    description: str
    date: Date = Field(index=True)
    frequency: str | None = None
    user_id: int | None = Field(default=None, foreign_key="users.id", index=True)


class BudgetRow(SQLModel, table=True):
    """One account's monthly budget for one category in the "budgets" table (the same every month)."""

    __tablename__ = "budgets"
    __table_args__ = (UniqueConstraint("user_id", "category", name="uq_budgets_user_id_category"),)

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    category: str  # stored lowercase, like the expenses' categories
    amount: float
