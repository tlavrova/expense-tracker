"""The expense endpoints: list, add, delete, summary and the AI category suggestion."""

from __future__ import annotations

import datetime
from typing import Literal

from fastapi import APIRouter, HTTPException, Query, Response, status

import ai_helper
import storage
from models import Expense, ExpenseTracker, RecurringExpense
from schemas import ExpenseOut, NewExpense, Suggestion, SuggestionRequest, Summary

router = APIRouter()


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


@router.get("/expenses", response_model=list[ExpenseOut], response_model_exclude_none=True)
def list_expenses(
    category: str | None = None,
    month: str | None = Query(None, description="YYYY-MM", examples=["2026-11"]),
    sort: Literal["amount", "date"] | None = None,
) -> list[ExpenseOut]:
    """All expenses in the order added; optionally only one category and/or month, and sorted."""
    tracker = storage.load()
    if category:
        tracker = ExpenseTracker(tracker.filter_by_category(category))
    if month:
        try:
            first_day = datetime.datetime.strptime(month, "%Y-%m")
        except ValueError:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT, "month must be YYYY-MM, for example 2026-11."
            ) from None
        tracker = ExpenseTracker(list(tracker.expenses_in_month(first_day.year, first_day.month)))
    return [to_out(expense) for expense in tracker.sorted_by(sort)]


@router.post(
    "/expenses",
    status_code=status.HTTP_201_CREATED,
    response_model=ExpenseOut,
    response_model_exclude_none=True,
)
def add_expense(new: NewExpense) -> ExpenseOut:
    """Save an expense. The same rules as the CLI apply; breaking one gives 422 with the reason."""
    try:
        if new.frequency:
            expense: Expense = RecurringExpense(
                new.amount, new.category, new.description, new.date, new.frequency.strip().lower()
            )
        else:
            expense = Expense(new.amount, new.category, new.description, new.date)
    except ValueError as error:  # InvalidAmountError is a ValueError too
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from None
    return to_out(storage.add(expense))


@router.delete("/expenses/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(expense_id: int) -> Response:
    if not storage.delete(expense_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"No expense with id {expense_id}.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/summary", response_model=Summary, response_model_by_alias=True)
def summary() -> Summary:
    """Totals per category (added up by the database) and the overall total."""
    totals = storage.totals_by_category()
    return Summary(totals_by_category=totals, total=sum(totals.values()))


@router.post("/suggest-category", response_model=Suggestion)
def suggest_category(request: SuggestionRequest) -> Suggestion:
    """Gemini's category for a description; 503 with the reason when the AI isn't available."""
    try:
        return Suggestion(category=ai_helper.suggest_category(request.description))
    except ai_helper.AIUnavailableError as error:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(error)) from None
