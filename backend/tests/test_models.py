"""The rules every expense follows, in the CLI and the API alike (models.py)."""

from datetime import date

import pytest

from models import Expense, ExpenseTracker, InvalidAmountError, RecurringExpense


def test_a_date_string_becomes_a_date_and_the_category_is_cleaned():
    expense = Expense(12.5, " Food ", "Lunch", "2026-11-02")
    assert expense.date == date(2026, 11, 2)
    assert expense.category == "food"


@pytest.mark.parametrize("amount", [0, -1, float("inf"), float("nan")])
def test_amounts_must_be_positive_numbers(amount):
    with pytest.raises(InvalidAmountError):
        Expense(amount, "food", "Lunch", "2026-11-02")


@pytest.mark.parametrize(
    ("description", "category", "day"),
    [(" ", "food", "2026-11-02"), ("Lunch", " ", "2026-11-02"), ("Lunch", "food", "2026-02-30")],
)
def test_description_category_and_date_must_be_real(description, category, day):
    with pytest.raises(ValueError):
        Expense(1, category, description, day)


def test_recurring_expenses_need_a_known_frequency():
    assert RecurringExpense(900, "housing", "Rent", "2026-10-01", "monthly").frequency == "monthly"
    with pytest.raises(ValueError, match="Frequency"):
        RecurringExpense(900, "housing", "Rent", "2026-10-01", "daily")


def tracker() -> ExpenseTracker:
    return ExpenseTracker(
        [
            Expense(32.5, "transport", "Uber", "2026-11-01", id=1),
            Expense(900, "housing", "Rent", "2026-10-01", id=2),
            Expense(12, "food", "Lunch", "2026-11-02", id=3),
        ]
    )


def test_totals_and_statistics():
    expenses = tracker()
    assert expenses.total() == 944.5
    assert expenses.average() == pytest.approx(314.83, abs=0.01)
    assert expenses.largest().description == "Rent"
    assert expenses.categories() == {"transport", "housing", "food"}
    assert ExpenseTracker().average() == 0.0


def test_sorting_filtering_and_months():
    expenses = tracker()
    assert [e.id for e in expenses.sorted_by("amount")] == [2, 1, 3]
    assert [e.id for e in expenses.sorted_by("date")] == [2, 1, 3]
    assert [e.id for e in expenses.sorted_by()] == [1, 2, 3]
    with pytest.raises(ValueError):
        expenses.sorted_by("name")
    assert [e.id for e in expenses.filter_by_category(" FOOD ")] == [3]
    assert [e.id for e in expenses.expenses_in_month(2026, 11)] == [1, 3]


def test_remove_by_id():
    expenses = tracker()
    expenses.remove(2)
    assert [e.id for e in expenses.expenses] == [1, 3]
