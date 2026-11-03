"""Load and save expenses as JSON.

Conversion between Expense objects and plain dicts lives here, so models.py doesn't depend on
the file format. Nothing here reads input or prints.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict
from pathlib import Path
from typing import Any

from models import Expense, ExpenseTracker, RecurringExpense

DEFAULT_PATH = Path(__file__).parent / "expenses.json"


class StorageError(Exception):
    """Raised when the data file can't be read or contains invalid data."""


def expense_to_dict(expense: Expense) -> dict[str, Any]:
    """Plain dict for JSON. RecurringExpense also has a "frequency" key."""
    return asdict(expense)


def expense_from_dict(data: dict[str, Any]) -> Expense:
    """Build an Expense, or a RecurringExpense when "frequency" is present. Validates the values."""
    if "frequency" in data:
        return RecurringExpense(**data)
    return Expense(**data)


def load(path: Path = DEFAULT_PATH) -> ExpenseTracker:
    """Load expenses from the file; a missing file means no expenses yet."""
    if not path.exists():
        return ExpenseTracker()
    try:
        with path.open(encoding="utf-8") as file:
            items = json.load(file)
        return ExpenseTracker([expense_from_dict(item) for item in items])
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as error:
        raise StorageError(f"Can't read {path}: {error}") from error


def save(tracker: ExpenseTracker, path: Path = DEFAULT_PATH) -> None:
    """Write all expenses to the file.

    Writes to a temporary file first and then replaces the real one, so a crash halfway through
    never leaves a half-written file behind.
    """
    items = [expense_to_dict(expense) for expense in tracker.expenses]
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8") as file:
        json.dump(items, file, indent=2, ensure_ascii=False)
    os.replace(temporary, path)
