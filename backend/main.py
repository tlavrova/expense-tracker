# Stage 3: Functions — menu actions as functions, sorting with sorted() + lambda.

from datetime import date


def add_expense(expenses):
    """Ask for an expense, add it to the list and return it."""
    description = input("Description: ").strip()
    amount = float(input("Amount: "))
    category = input("Category: ").strip().lower()
    when = input("Date (YYYY-MM-DD, empty for today): ").strip()
    if not when:
        when = date.today().isoformat()
    expense = {
        "amount": amount,
        "category": category,
        "description": description,
        "date": when,
    }
    expenses.append(expense)
    print("✅ Saved.")
    return expense


def total_spent(expenses):
    """Sum of all amounts."""
    return sum(expense["amount"] for expense in expenses)


def totals_by_category(expenses):
    """Return a dict: category -> total amount."""
    totals = {}
    for expense in expenses:
        category = expense["category"]
        totals[category] = totals.get(category, 0) + expense["amount"]
    return totals


def sort_expenses(expenses, by):
    """Return a new sorted list: by "amount" (largest first) or "date" (oldest first)."""
    if by == "amount":
        return sorted(expenses, key=lambda expense: expense["amount"], reverse=True)
    if by == "date":
        return sorted(expenses, key=lambda expense: expense["date"])
    return list(expenses)


def filter_by_category(expenses, category):
    """Return only the expenses in the given category (case-insensitive)."""
    category = category.strip().lower()
    return [expense for expense in expenses if expense["category"] == category]


def print_expenses(expenses):
    """Print a numbered list of expenses and their total."""
    if not expenses:
        print("No expenses.")
        return
    for number, expense in enumerate(expenses, start=1):
        print(
            f"{number}. {expense['date']}  {expense['description']} — "
            f"{expense['amount']:.2f} ({expense['category']})"
        )
    print(f"Total spent: {total_spent(expenses):.2f}")


def show_all(expenses):
    """Print all expenses, optionally sorted by amount or date."""
    if not expenses:
        print("No expenses yet.")
        return
    order = input("Sort by (a)mount, (d)ate, or Enter for as entered: ").strip().lower()
    if order == "a":
        expenses = sort_expenses(expenses, "amount")
    elif order == "d":
        expenses = sort_expenses(expenses, "date")
    print_expenses(expenses)


def show_summary(expenses):
    """Print totals per category, the overall total and the unique categories."""
    if not expenses:
        print("No expenses yet.")
        return
    totals = totals_by_category(expenses)
    categories = set(totals)  # unique categories
    print("Totals per category:")
    for category in sorted(totals):
        print(f"  {category}: {totals[category]:.2f}")
    print(f"Total spent: {total_spent(expenses):.2f}")
    print(f"Categories ({len(categories)}): {', '.join(sorted(categories))}")


def show_filtered(expenses):
    """Ask for a category and print only its expenses."""
    if not expenses:
        print("No expenses yet.")
        return
    category = input("Category: ")
    print_expenses(filter_by_category(expenses, category))


def main():
    expenses = []  # list of dicts: {"amount", "category", "description", "date"}
    print("=== Expense Tracker ===")
    while True:
        print()
        print("1) Add expense   2) Show all   3) Summary   4) Filter   5) Quit")
        choice = input("> ").strip()
        if choice == "1":
            add_expense(expenses)
        elif choice == "2":
            show_all(expenses)
        elif choice == "3":
            show_summary(expenses)
        elif choice == "4":
            show_filtered(expenses)
        elif choice == "5":
            print("Bye!")
            break
        else:
            print("Please choose 1, 2, 3, 4 or 5.")


if __name__ == "__main__":
    main()
