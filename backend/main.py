"""Command-line menu for the expense tracker. All user input and printing lives here."""

from __future__ import annotations

from datetime import date

from models import Expense, ExpenseTracker, RecurringExpense


def add_expense(tracker: ExpenseTracker) -> Expense:
    """Ask for an expense, add it to the tracker and return it."""
    description = input("Description: ").strip()
    amount = float(input("Amount: "))
    category = input("Category: ").strip().lower()
    when = input("Date (YYYY-MM-DD, empty for today): ").strip() or date.today().isoformat()
    frequency = input("Repeats (weekly/monthly/yearly, empty if not): ").strip().lower()

    expense: Expense
    if frequency:
        expense = RecurringExpense(amount, category, description, when, frequency)
    else:
        expense = Expense(amount, category, description, when)
    tracker.add(expense)
    print("✅ Saved.")
    return expense


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
    category = input("Category: ")
    print_expenses(tracker.filter_by_category(category))


def main() -> None:
    tracker = ExpenseTracker()
    actions = {
        "1": add_expense,
        "2": show_all,
        "3": show_summary,
        "4": show_filtered,
    }
    print("=== Expense Tracker ===")
    while True:
        print()
        print("1) Add expense   2) Show all   3) Summary   4) Filter   5) Quit")
        choice = input("> ").strip()
        if choice == "5":
            print("Bye!")
            break
        action = actions.get(choice)
        if action:
            action(tracker)
        else:
            print("Please choose 1, 2, 3, 4 or 5.")


if __name__ == "__main__":
    main()
