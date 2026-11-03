"""The screens of the command-line app: one function per menu option.

Each screen asks for what it needs (prompts.py), works with the tracker (models.py) and prints
the result. Screens are wrapped in @log_action so every action ends up in the log.
"""

from __future__ import annotations

from datetime import date
from typing import Iterable

import storage
from decorators import log_action
from models import Expense, ExpenseTracker, RecurringExpense
from prompts import ask_amount, ask_date, ask_frequency, ask_month, ask_text


@log_action
def add_expense(tracker: ExpenseTracker) -> None:
    """Ask for an expense, add it to the tracker and save."""
    description = ask_text("Description: ")
    amount = ask_amount()
    category = ask_text("Category: ").lower()
    when = ask_date()
    frequency = ask_frequency()

    expense: Expense
    if frequency:
        expense = RecurringExpense(amount, category, description, when, frequency)
    else:
        expense = Expense(amount, category, description, when)
    tracker.add(expense)
    try:
        storage.save(tracker)
    except OSError as error:
        print(f"⚠️  Added, but couldn't save to {storage.DEFAULT_PATH}: {error}")
        return
    print("✅ Saved.")


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
def show_all(tracker: ExpenseTracker) -> None:
    """Print all expenses, optionally sorted by amount or date."""
    if not tracker:
        print("No expenses yet.")
        return
    order = input("Sort by (a)mount, (d)ate, or Enter for as entered: ").strip().lower()
    key = {"a": "amount", "d": "date"}.get(order, "")
    print_expenses(tracker.sorted_by(key))


@log_action
def show_summary(tracker: ExpenseTracker) -> None:
    """Print totals per category, the overall total and the unique categories."""
    if not tracker:
        print("No expenses yet.")
        return
    totals = tracker.totals_by_category()
    print("Totals per category:")
    for category in sorted(totals):
        print(f"  {category}: {totals[category]:.2f}")
    print(f"Total spent: {tracker.total():.2f}")
    categories = sorted(tracker.categories())
    print(f"Categories ({len(categories)}): {', '.join(categories)}")


@log_action
def show_filtered(tracker: ExpenseTracker) -> None:
    """Ask for a category and print only its expenses."""
    if not tracker:
        print("No expenses yet.")
        return
    category = ask_text("Category: ")
    print_expenses(tracker.filter_by_category(category))


@log_action
def show_month(tracker: ExpenseTracker) -> None:
    """Ask for a month and print its expenses, read one at a time from a generator."""
    if not tracker:
        print("No expenses yet.")
        return
    year, month = ask_month()
    print(f"{date(year, month, 1):%B %Y}:")
    print_expenses(tracker.expenses_in_month(year, month))


@log_action
def show_statistics(tracker: ExpenseTracker) -> None:
    """Print counts per category, average and largest expense, and totals per month."""
    if not tracker:
        print("No expenses yet.")
        return
    print(f"Expenses: {len(tracker)}   Average: {tracker.average():.2f}")
    print(f"Largest: {tracker.largest()}")
    print("Most frequent categories:")
    for category, count in tracker.count_by_category().most_common():
        print(f"  {category}: {count}")
    print("Totals per month:")
    for month, total in tracker.totals_by_month().items():
        print(f"  {month}: {total:.2f}")
