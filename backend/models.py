"""Expense data classes and the tracker that holds them.

Nothing here reads input or prints, so the CLI (main.py), tests and the API can all reuse it.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date as Date

FREQUENCIES = ("weekly", "monthly", "yearly")


class InvalidAmountError(ValueError):
    """Raised when an amount is zero, negative or not a real number."""


def validate_amount(amount: float) -> float:
    """Return the amount if it is a positive, finite number; otherwise raise InvalidAmountError."""
    if not math.isfinite(amount) or amount <= 0:
        raise InvalidAmountError(f"Amount must be greater than zero, got {amount}.")
    return amount


def validate_date(value: str) -> str:
    """Return the date if it is a real YYYY-MM-DD date; otherwise raise ValueError."""
    try:
        Date.fromisoformat(value)
    except ValueError:
        raise ValueError(f"Date must be a real date as YYYY-MM-DD, got {value!r}.") from None
    return value


@dataclass
class Expense:
    amount: float
    category: str
    description: str
    date: str  # "YYYY-MM-DD"

    def __post_init__(self) -> None:
        validate_amount(self.amount)
        validate_date(self.date)
        if not self.description.strip():
            raise ValueError("Description must not be empty.")
        if not self.category.strip():
            raise ValueError("Category must not be empty.")

    def __str__(self) -> str:
        return f"{self.date}  {self.description} — {self.amount:.2f} ({self.category})"


@dataclass
class RecurringExpense(Expense):
    frequency: str  # one of FREQUENCIES

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.frequency not in FREQUENCIES:
            raise ValueError(f"Frequency must be one of {', '.join(FREQUENCIES)}, got {self.frequency!r}.")

    def __str__(self) -> str:
        return f"{super().__str__()} 🔁 {self.frequency}"


class ExpenseTracker:
    """Holds the list of expenses and answers questions about them."""

    def __init__(self, expenses: list[Expense] | None = None) -> None:
        self.expenses: list[Expense] = list(expenses or [])

    def __len__(self) -> int:
        return len(self.expenses)

    def add(self, expense: Expense) -> None:
        self.expenses.append(expense)

    def total(self) -> float:
        return sum(expense.amount for expense in self.expenses)

    def totals_by_category(self) -> dict[str, float]:
        totals: dict[str, float] = {}
        for expense in self.expenses:
            totals[expense.category] = totals.get(expense.category, 0) + expense.amount
        return totals

    def categories(self) -> set[str]:
        return {expense.category for expense in self.expenses}

    def sorted_by(self, key: str) -> list[Expense]:
        """Return a new list sorted by "amount" (largest first) or "date" (oldest first)."""
        if key == "amount":
            return sorted(self.expenses, key=lambda expense: expense.amount, reverse=True)
        if key == "date":
            return sorted(self.expenses, key=lambda expense: expense.date)
        return list(self.expenses)

    def filter_by_category(self, category: str) -> list[Expense]:
        category = category.strip().lower()
        return [expense for expense in self.expenses if expense.category == category]
