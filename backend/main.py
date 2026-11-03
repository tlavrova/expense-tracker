"""Command-line menu for the expense tracker: screens and the menu loop.

Data rules live in models.py, the JSON file in storage.py, input helpers in prompts.py and
the @log_action decorator in decorators.py.
"""

from __future__ import annotations

import logging
import sys
from datetime import date
from pathlib import Path
from typing import Iterable

import storage
from decorators import log_action
from models import Expense, ExpenseTracker, RecurringExpense
from prompts import ask_amount, ask_date, ask_frequency, ask_month, ask_text

LOG_PATH = Path(__file__).parent / "expenses.log"


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


def main() -> None:
    logging.basicConfig(
        filename=LOG_PATH,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        encoding="utf-8",
    )
    try:
        tracker = storage.load()
    except storage.StorageError as error:
        # Stop instead of starting empty: saving would overwrite the user's data.
        logging.getLogger("expense_tracker").error("%s", error)
        print(f"❌ {error}")
        print("Fix or move the file, then start again.")
        sys.exit(1)

    actions = {
        "1": add_expense,
        "2": show_all,
        "3": show_summary,
        "4": show_filtered,
        "5": show_month,
        "6": show_statistics,
    }
    print("=== Expense Tracker ===")
    if tracker:
        print(f"Loaded {len(tracker)} expense(s).")
    try:
        while True:
            print()
            print("1) Add expense   2) Show all   3) Summary   4) Filter")
            print("5) Month   6) Statistics   7) Quit")
            choice = input("> ").strip()
            if choice == "7":
                break
            action = actions.get(choice)
            if action:
                action(tracker)
            else:
                print("Please choose 1–7.")
    except (KeyboardInterrupt, EOFError):  # Ctrl+C or Ctrl+D
        print()
    print("Bye!")


if __name__ == "__main__":
    main()
