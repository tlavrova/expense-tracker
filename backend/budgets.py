"""One account's monthly budgets: category -> amount, the same every month.

Only website accounts have budgets (the command-line app has none). Categories are stored
lowercase without surrounding spaces, like the expenses' categories, so "Food" and "food" are the
same budget. The amount follows the same rule as an expense's (greater than zero).
"""

from __future__ import annotations

from sqlalchemy import Engine
from sqlmodel import select

import database
from tables import BudgetRow
from models import validate_amount


def normalize_category(category: str) -> str:
    """The same spelling the expenses use; ValueError if nothing is left."""
    cleaned = category.strip().lower()
    if not cleaned:
        raise ValueError("Category must not be empty.")
    return cleaned


def list_budgets(*, owner: int, engine: Engine | None = None) -> dict[str, float]:
    """Category -> monthly amount, A to Z."""
    statement = select(BudgetRow).where(BudgetRow.user_id == owner).order_by(BudgetRow.category)
    with database.open_session("read the budgets", engine) as session:
        return {row.category: row.amount for row in session.exec(statement)}


def set_budget(category: str, amount: float, *, owner: int, engine: Engine | None = None) -> tuple[str, float]:
    """Create or change the budget for this category; returns the saved (category, amount).

    ValueError (InvalidAmountError for the amount) if the category is empty or the amount isn't > 0.
    """
    category = normalize_category(category)
    amount = validate_amount(amount)
    with database.open_session("save the budget", engine) as session:
        row = _find(session, owner, category) or BudgetRow(user_id=owner, category=category, amount=amount)
        row.amount = amount
        session.add(row)
        session.commit()
    return category, amount


def delete_budget(category: str, *, owner: int, engine: Engine | None = None) -> bool:
    """Remove the budget for this category. False if there is none."""
    with database.open_session("delete the budget", engine) as session:
        row = _find(session, owner, category.strip().lower())
        if row is None:
            return False
        session.delete(row)
        session.commit()
    return True


def _find(session, owner: int, category: str) -> BudgetRow | None:
    statement = select(BudgetRow).where(BudgetRow.user_id == owner, BudgetRow.category == category)
    return session.exec(statement).first()
