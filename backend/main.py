"""Command-line menu for the expense tracker: screens and the menu loop.

Data rules live in models.py, the JSON file in storage.py, and input helpers in prompts.py.
"""

from __future__ import annotations

import sys

import storage
from models import Expense, ExpenseTracker, RecurringExpense
from prompts import ask_amount, ask_date, ask_frequency, ask_text


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


def print_expenses(expenses: list[Expense]) -> None:
    """Print a numbered list of expenses and their total."""
    if not expenses:
        print("No expenses.")
        return
    for number, expense in enumerate(expenses, start=1):
        print(f"{number}. {expense}")
    print(f"Total spent: {sum(expense.amount for expense in expenses):.2f}")


def show_all(tracker: ExpenseTracker) -> None:
    """Print all expenses, optionally sorted by amount or date."""
    if not tracker:
        print("No expenses yet.")
        return
    order = input("Sort by (a)mount, (d)ate, or Enter for as entered: ").strip().lower()
    key = {"a": "amount", "d": "date"}.get(order, "")
    print_expenses(tracker.sorted_by(key))


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


def show_filtered(tracker: ExpenseTracker) -> None:
    """Ask for a category and print only its expenses."""
    if not tracker:
        print("No expenses yet.")
        return
    category = ask_text("Category: ")
    print_expenses(tracker.filter_by_category(category))


def main() -> None:
    try:
        tracker = storage.load()
    except storage.StorageError as error:
        # Stop instead of starting empty: saving would overwrite the user's data.
        print(f"❌ {error}")
        print("Fix or move the file, then start again.")
        sys.exit(1)

    actions = {
        "1": add_expense,
        "2": show_all,
        "3": show_summary,
        "4": show_filtered,
    }
    print("=== Expense Tracker ===")
    if tracker:
        print(f"Loaded {len(tracker)} expense(s).")
    try:
        while True:
            print()
            print("1) Add expense   2) Show all   3) Summary   4) Filter   5) Quit")
            choice = input("> ").strip()
            if choice == "5":
                break
            action = actions.get(choice)
            if action:
                action(tracker)
            else:
                print("Please choose 1, 2, 3, 4 or 5.")
    except (KeyboardInterrupt, EOFError):  # Ctrl+C or Ctrl+D
        print()
    print("Bye!")


if __name__ == "__main__":
    main()
