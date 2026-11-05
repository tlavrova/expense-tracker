"""The screens of the command-line app: one function per menu option.

Each screen asks for what it needs (prompts.py), works with the tracker (models.py) and prints
the result. Screens are wrapped in @log_action so every action ends up in the log.
"""

from __future__ import annotations

import functools
from datetime import date
from typing import Any, Callable, Iterable, TypeVar

import ai_helper
import reports
import storage
from decorators import log_action
from models import CATEGORIES, Expense, ExpenseTracker, RecurringExpense
from prompts import (
    ask_amount,
    ask_date,
    ask_frequency,
    ask_month,
    ask_number,
    ask_text,
    ask_yes_no,
)

F = TypeVar("F", bound=Callable[..., Any])


def needs_expenses(screen: F) -> F:
    """Print "No expenses yet." and skip the screen when the tracker is empty.

    It prints, so it lives here with the screens instead of in decorators.py (shared with the API).
    Put it under @log_action, so an empty-tracker visit is still logged.
    """

    @functools.wraps(screen)
    def wrapper(tracker: ExpenseTracker, *args: Any, **kwargs: Any) -> Any:
        if not tracker:
            print("No expenses yet.")
            return None
        return screen(tracker, *args, **kwargs)

    return wrapper  # type: ignore[return-value]


@log_action
def add_expense(tracker: ExpenseTracker) -> None:
    """Ask for an expense, save it to the database and add it to the tracker."""
    description = ask_text("Description: ")
    amount = ask_amount()
    category = choose_category(description)
    when = ask_date()
    frequency = ask_frequency()

    expense: Expense
    if frequency:
        expense = RecurringExpense(amount, category, description, when, frequency)
    else:
        expense = Expense(amount, category, description, when)
    storage.add(expense, owner=storage.LOCAL)  # save first, so the tracker only holds what is in the database
    tracker.add(expense)
    print("✅ Saved.")


def choose_category(description: str) -> str:
    """Typed category, or an AI suggestion when left empty; falls back to typing it."""
    category = input("Category (leave empty for AI suggestion): ").strip().lower()
    if category:
        return category
    print("🤖 Asking Gemini… (Ctrl+C to skip)")
    try:
        suggestion = ai_helper.suggest_category(description)
    except ai_helper.AIUnavailableError as error:
        print(f"⚠️  No AI suggestion: {error}")
    except KeyboardInterrupt:
        print("Skipped.")
    else:
        if ask_yes_no(f"🤖 Suggested: {suggestion} — accept? (Y/n): "):
            return suggestion
    return ask_text(f"Category ({', '.join(CATEGORIES)}, or your own): ").lower()


def print_expenses(expenses: Iterable[Expense]) -> None:
    """Print a numbered list of expenses and their total. Works with lists and generators."""
    total = 0.0
    count = 0
    for count, expense in enumerate(expenses, start=1):
        print(f"{count}. {expense}")
        total += expense.amount
    if count == 0:
        print("No expenses.")
    else:
        print(f"Total spent: {total:.2f}")


@log_action
@needs_expenses
def show_all(tracker: ExpenseTracker) -> None:
    """Print all expenses, optionally sorted by amount or date."""
    order = input("Sort by (a)mount, (d)ate, or Enter for as entered: ").strip().lower()
    key = {"a": "amount", "d": "date"}.get(order)  # anything else: as entered
    print_expenses(tracker.sorted_by(key))


@log_action
@needs_expenses
def show_summary(tracker: ExpenseTracker) -> None:
    """Print totals per category, the overall total and the unique categories."""
    print("Totals per category:")
    for category, total in reports.totals_by_category(owner=storage.LOCAL).items():
        print(f"  {category}: {total:.2f}")
    print(f"Total spent: {tracker.total():.2f}")
    categories = sorted(tracker.categories())
    print(f"Categories ({len(categories)}): {', '.join(categories)}")


@log_action
@needs_expenses
def show_filtered(tracker: ExpenseTracker) -> None:
    """Ask for a category and print only its expenses."""
    category = ask_text("Category: ")
    print_expenses(tracker.filter_by_category(category))


@log_action
@needs_expenses
def show_month(tracker: ExpenseTracker) -> None:
    """Ask for a month and print its expenses, read one at a time from a generator."""
    year, month = ask_month()
    print(f"{date(year, month, 1):%B %Y}:")
    print_expenses(tracker.expenses_in_month(year, month))


@log_action
@needs_expenses
def show_statistics(tracker: ExpenseTracker) -> None:
    """Print counts per category, average and largest expense, and totals per month."""
    print(f"Expenses: {len(tracker)}   Average: {tracker.average():.2f}")
    print(f"Largest: {tracker.largest()}")
    print("Most frequent categories:")
    for category, count in tracker.count_by_category().most_common():
        print(f"  {category}: {count}")
    print("Totals per month:")
    for month, total in reports.totals_by_month(owner=storage.LOCAL).items():
        print(f"  {month}: {total:.2f}")


@log_action
@needs_expenses
def delete_expense(tracker: ExpenseTracker) -> None:
    """Show the numbered list, ask which expense to delete, confirm and delete it."""
    expenses = tracker.sorted_by()
    print_expenses(expenses)
    number = ask_number(f"Number to delete (1–{len(expenses)}, empty to cancel): ", len(expenses))
    if number is None:
        print("Cancelled.")
        return
    expense = expenses[number - 1]
    if not ask_yes_no(f"Delete \"{expense}\"? (y/N): ", default=False):
        print("Cancelled.")
        return
    assert expense.id is not None  # everything in the tracker came from the database
    if storage.delete(expense.id, owner=storage.LOCAL):
        print("🗑️  Deleted.")
    else:
        print("⚠️  It was already gone.")
    tracker.remove(expense.id)
