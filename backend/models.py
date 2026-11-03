"""Expense data classes and the tracker that holds them.

Nothing here reads input or prints, so the CLI (main.py), tests and the API can all reuse it.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Expense:
    amount: float
    category: str
    description: str
    date: str  # "YYYY-MM-DD"

    def __str__(self) -> str:
        return f"{self.date}  {self.description} — {self.amount:.2f} ({self.category})"


@dataclass
class RecurringExpense(Expense):
    frequency: str  # e.g. "weekly", "monthly", "yearly"

    def __str__(self) -> str:
        return f"{super().__str__()} 🔁 {self.frequency}"


class ExpenseTracker:
    """Holds the list of expenses and answers questions about them."""

    def __init__(self) -> None:
        self.expenses: list[Expense] = []

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
