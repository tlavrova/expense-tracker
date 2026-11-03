# Stage 1: Basics — menu loop, expenses kept in a list, total spent.

expenses = []  # each expense is [amount, category, description]

print("=== Expense Tracker ===")

while True:
    print()
    print("1) Add expense   2) Show all   3) Quit")
    choice = input("> ").strip()

    if choice == "1":
        description = input("Description: ").strip()
        amount = float(input("Amount: "))
        category = input("Category: ").strip().lower()
        expenses.append([amount, category, description])
        print("✅ Saved.")

    elif choice == "2":
        if not expenses:
            print("No expenses yet.")
        else:
            total = 0
            for number, expense in enumerate(expenses, start=1):
                amount, category, description = expense
                print(f"{number}. {description} — {amount:.2f} ({category})")
                total += amount
            print(f"Total spent: {total:.2f}")

    elif choice == "3":
        print("Bye!")
        break

    else:
        print("Please choose 1, 2 or 3.")
