"""The one-time move from expenses.json (stages 6–8) into the database (stage 8a).

Kept apart from storage.py because it only matters once; when nobody has an old expenses.json any
more, this file can simply be deleted.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from sqlalchemy import Engine
from sqlmodel import select

import database
from database import ExpenseRow, StorageError
from models import Expense, RecurringExpense
from storage import LOCAL, row_from_expense

JSON_PATH = Path(__file__).parent / "expenses.json"

logger = logging.getLogger("expense_tracker")


def import_json(path: Path | None = None, engine: Engine | None = None) -> int:
    """Move the expenses from the old expenses.json into the database, once.

    Only into an empty database, so nothing is ever imported twice (for example when the app
    stopped after importing but before renaming). All rows go in in one transaction, then the file
    is renamed to expenses.json.imported so the next start doesn't import it again.
    Returns how many expenses were imported (0: no file, or the database already has expenses).
    """
    path = path or JSON_PATH  # read here, not as a default, so tests can point it elsewhere
    if not path.exists():
        return 0
    with database.open_session("check the database", engine) as session:
        has_expenses = session.exec(select(ExpenseRow.id).limit(1)).first() is not None
    if has_expenses:
        logger.warning("Not importing %s: the database already has expenses.", path)
        return 0
    try:
        with path.open(encoding="utf-8") as file:
            items = json.load(file)
        expenses = [
            RecurringExpense(**item) if "frequency" in item else Expense(**item) for item in items
        ]
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as error:
        raise StorageError(f"Can't read {path}: {error}") from error

    with database.open_session(f"import {path}", engine) as session:
        session.add_all(row_from_expense(expense, LOCAL) for expense in expenses)  # the CLI's own
        session.commit()
    path.rename(path.with_name(path.name + ".imported"))
    return len(expenses)
