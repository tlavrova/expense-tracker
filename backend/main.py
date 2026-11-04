"""Start the command-line expense tracker: set up logging, load the data, run the menu.

What each menu option does lives in screens.py.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import screens
import storage

LOG_PATH = Path(__file__).parent / "expenses.log"

# Menu label and the screen it opens. Numbers are assigned in this order; Quit comes last.
MENU = [
    ("Add expense", screens.add_expense),
    ("Show all", screens.show_all),
    ("Summary", screens.show_summary),
    ("Filter", screens.show_filtered),
    ("Month", screens.show_month),
    ("Statistics", screens.show_statistics),
    ("Delete", screens.delete_expense),
]


def print_menu() -> None:
    labels = [f"{number}) {label}" for number, (label, _) in enumerate(MENU, start=1)]
    labels.append(f"{len(MENU) + 1}) Quit")
    print()
    print("   ".join(labels[:4]))
    print("   ".join(labels[4:]))


def main() -> None:
    logging.basicConfig(
        filename=LOG_PATH,
        level=logging.WARNING,  # other libraries (Gemini SDK, HTTP client): warnings only
        format="%(asctime)s %(levelname)s %(message)s",
        encoding="utf-8",
    )
    logging.getLogger("expense_tracker").setLevel(logging.INFO)  # our own actions in full
    try:
        imported = storage.import_json()  # once: the expenses.json used before stage 8a
        tracker = storage.load()
    except storage.StorageError as error:
        logging.getLogger("expense_tracker").error("%s", error)
        print(f"❌ {error}")
        print("Check DATABASE_URL or expenses.json, then start again.")
        sys.exit(1)

    actions = {str(number): screen for number, (_, screen) in enumerate(MENU, start=1)}
    quit_choice = str(len(MENU) + 1)

    print("=== Expense Tracker ===")
    if imported:
        print(f"Moved {imported} expense(s) from expenses.json into the database.")
    if tracker:
        print(f"Loaded {len(tracker)} expense(s).")
    try:
        while True:
            print_menu()
            choice = input("> ").strip()
            if choice == quit_choice:
                break
            action = actions.get(choice)
            if action:
                try:
                    action(tracker)
                except storage.StorageError as error:  # e.g. the database went away; keep running
                    print(f"❌ {error}")
            else:
                print(f"Please choose 1–{quit_choice}.")
    except (KeyboardInterrupt, EOFError):  # Ctrl+C or Ctrl+D
        print()
    print("Bye!")


if __name__ == "__main__":
    main()
