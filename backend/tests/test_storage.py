"""Expense queries: each owner (the CLI, or one account) only ever sees its own rows."""

import pytest

import storage
from models import Expense, RecurringExpense


def add_some(owner):
    storage.add(Expense(32.5, "transport", "Uber", "2026-11-01"), owner=owner)
    storage.add(RecurringExpense(900, "housing", "Rent", "2026-10-01", "monthly"), owner=owner)
    storage.add(Expense(18, "transport", "Taxi", "2026-11-03"), owner=owner)


def test_owners_never_see_each_others_expenses(two_users):
    ana, bob = two_users
    add_some(ana)
    storage.add(Expense(7, "food", "Bob's lunch", "2026-11-02"), owner=bob)
    storage.add(Expense(3.5, "food", "CLI coffee", "2026-11-02"), owner=storage.LOCAL)
    assert [e.description for e in storage.list_expenses(owner=ana)] == ["Uber", "Rent", "Taxi"]
    assert [e.description for e in storage.list_expenses(owner=bob)] == ["Bob's lunch"]
    assert [e.description for e in storage.load(owner=storage.LOCAL).expenses] == ["CLI coffee"]


def test_delete_only_works_for_the_owner(two_users):
    ana, bob = two_users
    expense = storage.add(Expense(7, "food", "Bob's lunch", "2026-11-02"), owner=bob)
    assert storage.delete(expense.id, owner=ana) is False
    assert storage.delete(expense.id, owner=storage.LOCAL) is False
    assert storage.delete(expense.id, owner=bob) is True
    assert storage.list_expenses(owner=bob) == []


def test_filters_and_sorting_happen_in_the_database(two_users):
    ana, _ = two_users
    add_some(ana)
    by_amount = storage.list_expenses(owner=ana, category="TRANSPORT", sort="amount")
    assert [(e.description, e.amount) for e in by_amount] == [("Uber", 32.5), ("Taxi", 18.0)]
    november = storage.list_expenses(owner=ana, year_month=(2026, 11), sort="date")
    assert [e.description for e in november] == ["Uber", "Taxi"]
    assert storage.list_expenses(owner=ana, year_month=(2025, 1)) == []


def test_recurring_expenses_come_back_as_recurring(two_users):
    ana, _ = two_users
    add_some(ana)
    rent = storage.list_expenses(owner=ana, category="housing")[0]
    assert isinstance(rent, RecurringExpense) and rent.frequency == "monthly"


def test_owner_is_required():
    with pytest.raises(TypeError):
        storage.list_expenses()  # no default, so no code can forget whose expenses it means


def test_get_and_update_only_the_owners_expense(two_users):
    ana, bob = two_users
    uber = storage.add(Expense(32.5, "transport", "Uber", "2026-11-01"), owner=ana)
    assert storage.get(uber.id, owner=ana).description == "Uber"
    assert storage.get(uber.id, owner=bob) is None
    assert storage.get(uber.id, owner=storage.LOCAL) is None

    rent = RecurringExpense(900, "housing", "Rent", "2026-10-01", "monthly")
    assert storage.update(uber.id, rent, owner=bob) is None  # Bob can't change Ana's expense
    assert storage.update(uber.id, rent, owner=ana).id == uber.id
    saved = storage.get(uber.id, owner=ana)
    assert (saved.description, saved.amount, saved.frequency) == ("Rent", 900, "monthly")

    storage.update(uber.id, Expense(32.5, "transport", "Uber", "2026-11-01"), owner=ana)
    assert not hasattr(storage.get(uber.id, owner=ana), "frequency")  # no longer repeats
    assert len(storage.list_expenses(owner=ana)) == 1
