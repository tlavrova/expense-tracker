"""Totals: added up by the database, and only over one owner's expenses."""

import reports
import storage
from models import Expense
from tests.test_storage import add_some


def test_totals_per_category_and_month(two_users):
    ana, _ = two_users
    add_some(ana)
    assert reports.totals_by_category(owner=ana) == {"housing": 900.0, "transport": 50.5}
    assert reports.totals_by_month(owner=ana) == {"2026-10": 900.0, "2026-11": 50.5}


def test_totals_only_count_the_owners_expenses(two_users):
    ana, bob = two_users
    add_some(ana)
    storage.add(Expense(7, "food", "Bob's lunch", "2026-11-02"), owner=bob)
    storage.add(Expense(3.5, "food", "CLI coffee", "2026-11-02"), owner=storage.LOCAL)
    assert reports.totals_by_category(owner=bob) == {"food": 7.0}
    assert reports.totals_by_category(owner=storage.LOCAL) == {"food": 3.5}
