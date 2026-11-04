"""Expense data classes and the tracker that holds them.

Nothing here reads input or prints, so the CLI (main.py), tests and the API can all reuse it.
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field
from datetime import date as Date
from typing import Iterator

FREQUENCIES = ("weekly", "monthly", "yearly")

# The categories the AI may suggest (stage 8). People can still type their own.
CATEGORIES = ("food", "transport", "housing", "entertainment", "shopping", "health", "other")


class InvalidAmountError(ValueError):
    """Raised when an amount is zero, negative or not a real number."""


def validate_amount(amount: float) -> float:
    """Return the amount if it is a positive, finite number; otherwise raise InvalidAmountError."""
    if not math.isfinite(amount) or amount <= 0:
        raise InvalidAmountError(f"Amount must be greater than zero, got {amount}.")
    return amount


def parse_date(value: str) -> Date:
    """Turn "YYYY-MM-DD" into a date; raise ValueError if it isn't a real date."""
    try:
        return Date.fromisoformat(value)
    except ValueError:
        raise ValueError(f"Date must be a real date as YYYY-MM-DD, got {value!r}.") from None


@dataclass
class Expense:
    amount: float
    category: str
    description: str
    date: Date  # a "YYYY-MM-DD" string is accepted and converted
    # Set by the database when the expense is saved (stage 8a); None until then.
    # Keyword-only, so it never shifts the positional fields, and ignored when comparing.
    id: int | None = field(default=None, kw_only=True, compare=False)

    def __post_init__(self) -> None:
        validate_amount(self.amount)
        if isinstance(self.date, str):
            self.date = parse_date(self.date)
        elif not isinstance(self.date, Date):
            raise TypeError(f"Date must be a date or a YYYY-MM-DD string, got {self.date!r}.")
        if not self.description.strip():
            raise ValueError("Description must not be empty.")
        self.category = self.category.strip().lower()  # "Food" and "food" are the same category
        if not self.category:
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

    def remove(self, expense_id: int) -> None:
        """Drop the expense with this id (after the database deleted it)."""
        self.expenses = [expense for expense in self.expenses if expense.id != expense_id]

    def total(self) -> float:
        return sum(expense.amount for expense in self.expenses)

    def count_by_category(self) -> Counter[str]:
        """How many expenses each category has; .most_common() sorts them."""
        return Counter(expense.category for expense in self.expenses)

    def average(self) -> float:
        """Average amount per expense; 0 when there are none."""
        return self.total() / len(self) if self.expenses else 0.0

    def largest(self) -> Expense | None:
        return max(self.expenses, key=lambda expense: expense.amount, default=None)

    def expenses_in_month(self, year: int, month: int) -> Iterator[Expense]:
        """Yield the expenses of one month, one at a time, without building a new list."""
        for expense in self.expenses:
            if expense.date.year == year and expense.date.month == month:
                yield expense

    def categories(self) -> set[str]:
        return {expense.category for expense in self.expenses}

    def sorted_by(self, key: str | None = None) -> list[Expense]:
        """Return a new list sorted by "amount" (largest first) or "date" (oldest first).

        None keeps the order they were entered in; any other key raises ValueError.
        """
        if key is None:
            return list(self.expenses)
        if key == "amount":
            return sorted(self.expenses, key=lambda expense: expense.amount, reverse=True)
        if key == "date":
            return sorted(self.expenses, key=lambda expense: expense.date)
        raise ValueError(f'Sort key must be "amount" or "date", got {key!r}.')

    def filter_by_category(self, category: str) -> list[Expense]:
        category = category.strip().lower()
        return [expense for expense in self.expenses if expense.category == category]
