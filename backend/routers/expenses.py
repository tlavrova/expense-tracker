"""The expense endpoints: list, get one, add, change and delete.

Every endpoint needs a logged-in user (security.CurrentUser) and only sees that user's own
expenses: another account's expense id answers 404, as if it didn't exist.
"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException, Query, Response, status

import storage
from models import Expense, RecurringExpense
from routers.params import parse_month
from schemas import ExpenseOut, NewExpense
from security import CurrentUser

router = APIRouter(tags=["expenses"])


def to_out(expense: Expense) -> ExpenseOut:
    assert expense.id is not None  # everything here came from the database
    return ExpenseOut(
        id=expense.id,
        amount=expense.amount,
        category=expense.category,
        description=expense.description,
        date=expense.date,
        frequency=getattr(expense, "frequency", None),
    )


def from_new(new: NewExpense) -> Expense:
    """The model checks the same rules as the CLI; breaking one gives 422 with the reason."""
    try:
        if new.frequency:
            return RecurringExpense(new.amount, new.category, new.description, new.date, new.frequency.strip().lower())
        return Expense(new.amount, new.category, new.description, new.date)
    except ValueError as error:  # InvalidAmountError is a ValueError too
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from None


def not_found(expense_id: int) -> HTTPException:
    return HTTPException(status.HTTP_404_NOT_FOUND, f"No expense with id {expense_id}.")


@router.get("/expenses", response_model=list[ExpenseOut], response_model_exclude_none=True)
def list_expenses(
    user: CurrentUser,
    category: str | None = None,
    month: str | None = Query(None, description="YYYY-MM", examples=["2026-11"]),
    sort: Literal["amount", "date"] | None = None,
) -> list[ExpenseOut]:
    """Your expenses in the order added; optionally only one category and/or month, and sorted."""
    year_month = parse_month(month)
    expenses = storage.list_expenses(owner=user.id, category=category, year_month=year_month, sort=sort)
    return [to_out(expense) for expense in expenses]


@router.post(
    "/expenses",
    status_code=status.HTTP_201_CREATED,
    response_model=ExpenseOut,
    response_model_exclude_none=True,
)
def add_expense(new: NewExpense, user: CurrentUser) -> ExpenseOut:
    """Save an expense. The same rules as the CLI apply; breaking one gives 422 with the reason."""
    return to_out(storage.add(from_new(new), owner=user.id))


@router.get("/expenses/{expense_id}", response_model=ExpenseOut, response_model_exclude_none=True)
def get_expense(expense_id: int, user: CurrentUser) -> ExpenseOut:
    """One of your expenses (the edit page loads it); 404 if it isn't yours or doesn't exist."""
    expense = storage.get(expense_id, owner=user.id)
    if expense is None:
        raise not_found(expense_id)
    return to_out(expense)


@router.put("/expenses/{expense_id}", response_model=ExpenseOut, response_model_exclude_none=True)
def update_expense(expense_id: int, new: NewExpense, user: CurrentUser) -> ExpenseOut:
    """Replace one of your expenses with these values: the same body and rules as adding one.

    Leaving out frequency makes it a one-off expense. 404 if it isn't yours or doesn't exist.
    """
    expense = storage.update(expense_id, from_new(new), owner=user.id)
    if expense is None:
        raise not_found(expense_id)
    return to_out(expense)


@router.delete("/expenses/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(expense_id: int, user: CurrentUser) -> Response:
    if not storage.delete(expense_id, owner=user.id):
        raise not_found(expense_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
