"""Budgets: stored per account, the same rules as expenses, and the month report next to them."""

import pytest

import budgets
import storage
from models import Expense

FOOD_LUNCH = {"amount": 12.5, "category": "food", "description": "Lunch", "date": "2026-11-02"}
FOOD_OCTOBER = {"amount": 40, "category": "food", "description": "Groceries", "date": "2026-10-30"}
UBER = {"amount": 32.5, "category": "transport", "description": "Uber", "date": "2026-11-01"}


def test_set_change_and_delete_a_budget(two_users):
    ana, bob = two_users
    assert budgets.set_budget(" Food ", 300, owner=ana) == ("food", 300.0)
    assert budgets.set_budget("food", 250, owner=ana) == ("food", 250.0)  # changed, not a second one
    budgets.set_budget("transport", 80, owner=ana)
    assert budgets.list_budgets(owner=ana) == {"food": 250.0, "transport": 80.0}
    assert budgets.list_budgets(owner=bob) == {}  # Ana's budgets are hers only
    assert budgets.delete_budget("food", owner=bob) is False
    assert budgets.delete_budget("FOOD", owner=ana) is True
    assert budgets.list_budgets(owner=ana) == {"transport": 80.0}


@pytest.mark.parametrize(("category", "amount", "message"), [("food", 0, "Amount must be greater than zero"),
                                                             (" ", 10, "Category must not be empty.")])
def test_budgets_follow_the_expense_rules(two_users, category, amount, message):
    with pytest.raises(ValueError, match=message):
        budgets.set_budget(category, amount, owner=two_users[0])


def test_budgets_api(client, sign_up):
    ana, bob = sign_up(), sign_up("bob@example.com", "bobs password")
    assert client.put("/budgets/Food", json={"amount": 300}, headers=ana).json() == {"category": "food", "amount": 300.0}
    client.put("/budgets/transport", json={"amount": 80}, headers=ana)
    assert client.get("/budgets", headers=ana).json() == [
        {"category": "food", "amount": 300.0},
        {"category": "transport", "amount": 80.0},
    ]
    assert client.get("/budgets", headers=bob).json() == []
    assert client.delete("/budgets/food", headers=bob).status_code == 404  # not Bob's
    assert client.delete("/budgets/food", headers=ana).status_code == 204
    answer = client.delete("/budgets/food", headers=ana)
    assert answer.status_code == 404 and answer.json() == {"detail": "No budget for 'food'."}
    assert client.get("/budgets").status_code == 401  # login required


@pytest.mark.parametrize(("body", "message"), [({"amount": -5}, "Amount must be greater than zero"),
                                               ({"amount": "lots"}, "amount: Input should be a valid number")])
def test_budgets_api_checks_the_amount(client, sign_up, body, message):
    answer = client.put("/budgets/food", json=body, headers=sign_up())
    assert answer.status_code == 422 and answer.json()["detail"].startswith(message)


def test_month_report_puts_spending_next_to_budgets(client, sign_up):
    ana = sign_up()
    for expense in (FOOD_LUNCH, FOOD_OCTOBER, UBER):
        client.post("/expenses", json=expense, headers=ana)
    client.put("/budgets/food", json={"amount": 300}, headers=ana)
    client.put("/budgets/health", json={"amount": 50}, headers=ana)  # nothing spent yet
    storage.add(Expense(99, "food", "CLI groceries", "2026-11-03"), owner=storage.LOCAL)  # not Ana's

    report = client.get("/reports/month?month=2026-11", headers=ana).json()
    assert report == {
        "month": "2026-11",
        "rows": [
            {"category": "food", "spent": 12.5, "budget": 300.0},  # October's groceries don't count
            {"category": "health", "spent": 0.0, "budget": 50.0},
            {"category": "transport", "spent": 32.5, "budget": None},  # spending without a budget
        ],
        "totalSpent": 45.0,
        "totalBudget": 350.0,
    }
    october = client.get("/reports/month?month=2026-10", headers=ana).json()
    assert october["rows"][0] == {"category": "food", "spent": 40.0, "budget": 300.0}  # the same budget every month


@pytest.mark.parametrize("query", ["", "?month=november", "?month=2026-13"])
def test_month_report_needs_a_proper_month(client, sign_up, query):
    answer = client.get(f"/reports/month{query}", headers=sign_up())
    assert answer.status_code == 422
