# Stage 2: Data structures — each expense is a dict, totals per category, unique categories as a set.

from datetime import date

expenses = []  # list of dicts: {"amount", "category", "description", "date"}

print("=== Expense Tracker ===")

while True:
    print()
    print("1) Add expense   2) Show all   3) Summary   4) Quit")
    choice = input("> ").strip()

    if choice == "1":
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

    elif choice == "2":
        if not expenses:
            print("No expenses yet.")
        else:
            total = 0
            for number, expense in enumerate(expenses, start=1):
                print(
                    f"{number}. {expense['date']}  {expense['description']} — "
                    f"{expense['amount']:.2f} ({expense['category']})"
                )
                total += expense["amount"]
            print(f"Total spent: {total:.2f}")

    elif choice == "3":
        if not expenses:
            print("No expenses yet.")
        else:
            totals = {}  # category -> total amount
            categories = set()  # unique categories
            for expense in expenses:
                category = expense["category"]
                totals[category] = totals.get(category, 0) + expense["amount"]
                categories.add(category)

            print("Totals per category:")
            for category in sorted(totals):
                print(f"  {category}: {totals[category]:.2f}")
            print(f"Total spent: {sum(totals.values()):.2f}")
            print(f"Categories ({len(categories)}): {', '.join(sorted(categories))}")

    elif choice == "4":
        print("Bye!")
        break

    else:
        print("Please choose 1, 2, 3 or 4.")
