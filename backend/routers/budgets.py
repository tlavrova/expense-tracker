"""Your monthly budgets: one amount per category, the same every month (budgets.py stores them).

How much of a budget is used in a given month is in GET /reports/month (routers/reports.py).
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response, status

import budgets
from schemas import Budget, BudgetAmount
from security import CurrentUser

router = APIRouter(prefix="/budgets", tags=["budgets"])


@router.get("", response_model=list[Budget])
def list_budgets(user: CurrentUser) -> list[Budget]:
    """Your budgets, A to Z by category."""
    assert user.id is not None
    return [Budget(category=c, amount=a) for c, a in budgets.list_budgets(owner=user.id).items()]


@router.put("/{category}", response_model=Budget)
def set_budget(category: str, body: BudgetAmount, user: CurrentUser) -> Budget:
    """Set or change the budget for a category (stored lowercase); 422 if the amount isn't > 0."""
    assert user.id is not None
    try:
        saved, amount = budgets.set_budget(category, body.amount, owner=user.id)
    except ValueError as error:  # InvalidAmountError is a ValueError too
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from None
    return Budget(category=saved, amount=amount)


@router.delete("/{category}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget(category: str, user: CurrentUser) -> Response:
    """Remove the budget for a category; 404 if it has none."""
    assert user.id is not None
    if not budgets.delete_budget(category, owner=user.id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"No budget for {category.strip().lower()!r}.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
