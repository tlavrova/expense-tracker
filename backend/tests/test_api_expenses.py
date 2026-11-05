"""The expense endpoints, as the Angular app uses them."""

import pytest

import ai_helper
import storage
from models import Expense

RENT = {"amount": 900, "category": "Housing", "description": "Rent", "date": "2026-10-01", "frequency": "MONTHLY"}
UBER = {"amount": 32.5, "category": "transport", "description": "Uber", "date": "2026-11-01"}
TAXI = {"amount": 18, "category": "transport", "description": "Taxi", "date": "2026-11-03"}


@pytest.fixture
def ana(client, sign_up):
    headers = sign_up()
    for expense in (RENT, UBER, TAXI):
        assert client.post("/expenses", json=expense, headers=headers).status_code == 201
    return headers


def test_add_returns_the_saved_expense(client, sign_up):
    headers = sign_up()
    saved = client.post("/expenses", json=RENT, headers=headers).json()
    assert saved == {"id": saved["id"], "amount": 900.0, "category": "housing", "description": "Rent",
                     "date": "2026-10-01", "frequency": "monthly"}
    one_off = client.post("/expenses", json=UBER, headers=headers).json()
    assert "frequency" not in one_off  # left out, as the TypeScript type expects


def test_list_filters_and_sorts(client, ana):
    def descriptions(query=""):
        return [e["description"] for e in client.get(f"/expenses{query}", headers=ana).json()]

    assert descriptions() == ["Rent", "Uber", "Taxi"]
    assert descriptions("?category=TRANSPORT&sort=amount") == ["Uber", "Taxi"]
    assert descriptions("?month=2026-11&sort=date") == ["Uber", "Taxi"]
    assert descriptions("?sort=amount") == ["Rent", "Uber", "Taxi"]


def test_summary(client, ana):
    assert client.get("/summary", headers=ana).json() == {
        "totalsByCategory": {"housing": 900.0, "transport": 50.5},
        "total": 950.5,
    }


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"amount": 0}, "Amount must be greater than zero, got 0.0."),
        ({"amount": "abc"}, "amount: Input should be a valid number"),
        ({"date": "2026-02-30"}, "date: Input should be a valid date"),
        ({"frequency": "daily"}, "Frequency must be one of weekly, monthly, yearly"),
        ({"description": " "}, "Description must not be empty."),
    ],
)
def test_invalid_expenses_get_one_readable_message(client, sign_up, change, message):
    answer = client.post("/expenses", json={**UBER, **change}, headers=sign_up())
    assert answer.status_code == 422
    assert answer.json()["detail"].startswith(message)


@pytest.mark.parametrize(("query", "message"), [("?month=nov", "month must be YYYY-MM"), ("?sort=name", "sort: Input should be")])
def test_invalid_filters(client, sign_up, query, message):
    answer = client.get(f"/expenses{query}", headers=sign_up())
    assert answer.status_code == 422 and answer.json()["detail"].startswith(message)


def test_users_cannot_see_or_delete_each_others_expenses(client, ana, sign_up):
    bob = sign_up("bob@example.com", "bobs password")
    assert client.get("/expenses", headers=bob).json() == []
    assert client.get("/summary", headers=bob).json() == {"totalsByCategory": {}, "total": 0.0}
    anas_first = client.get("/expenses", headers=ana).json()[0]["id"]
    assert client.delete(f"/expenses/{anas_first}", headers=bob).status_code == 404
    assert client.delete(f"/expenses/{anas_first}", headers=ana).status_code == 204
    assert client.delete(f"/expenses/{anas_first}", headers=ana).status_code == 404


def test_get_and_change_one_expense(client, ana):
    uber = client.get("/expenses", headers=ana).json()[1]
    assert client.get(f"/expenses/{uber['id']}", headers=ana).json() == uber

    changed = client.put(f"/expenses/{uber['id']}", json={**UBER, "amount": 35, "category": "Travel", "frequency": "Weekly"},
                         headers=ana)
    assert changed.status_code == 200
    assert changed.json() == {**uber, "amount": 35.0, "category": "travel", "frequency": "weekly"}
    assert client.get(f"/expenses/{uber['id']}", headers=ana).json() == changed.json()

    one_off = client.put(f"/expenses/{uber['id']}", json=UBER, headers=ana).json()  # no frequency: no longer repeats
    assert "frequency" not in one_off
    assert [e["description"] for e in client.get("/expenses", headers=ana).json()] == ["Rent", "Uber", "Taxi"]  # same place


def test_changing_an_expense_checks_the_same_rules(client, ana):
    uber_id = client.get("/expenses", headers=ana).json()[1]["id"]
    answer = client.put(f"/expenses/{uber_id}", json={**UBER, "amount": -5}, headers=ana)
    assert answer.status_code == 422 and answer.json()["detail"].startswith("Amount must be greater than zero")
    assert client.get(f"/expenses/{uber_id}", headers=ana).json()["amount"] == 32.5  # unchanged


def test_users_cannot_see_or_change_each_others_expense(client, ana, sign_up):
    bob = sign_up("bob@example.com", "bobs password")
    anas_first = client.get("/expenses", headers=ana).json()[0]
    assert client.get(f"/expenses/{anas_first['id']}", headers=bob).status_code == 404
    answer = client.put(f"/expenses/{anas_first['id']}", json=UBER, headers=bob)
    assert answer.status_code == 404 and answer.json() == {"detail": f"No expense with id {anas_first['id']}."}
    assert client.get(f"/expenses/{anas_first['id']}", headers=ana).json() == anas_first  # untouched
    assert client.put("/expenses/999", json=UBER, headers=ana).status_code == 404


def test_the_command_line_apps_expenses_stay_out_of_the_website(client, sign_up):
    storage.add(Expense(3.5, "food", "CLI coffee", "2026-11-01"), owner=storage.LOCAL)
    assert client.get("/expenses", headers=sign_up()).json() == []


def test_suggest_category(client, sign_up, monkeypatch):
    monkeypatch.setattr(ai_helper, "suggest_category", lambda description: "transport")
    answer = client.post("/suggest-category", json={"description": "Uber to airport"}, headers=sign_up())
    assert answer.json() == {"category": "transport"}


def test_suggest_category_without_ai(client, sign_up):
    answer = client.post("/suggest-category", json={"description": "Uber"}, headers=sign_up())
    assert answer.status_code == 503 and answer.json() == {"detail": "GEMINI_API_KEY is not set."}


def test_cors_lets_the_angular_dev_server_send_the_token(client):
    answer = client.options("/expenses", headers={"Origin": "http://localhost:4200", "Access-Control-Request-Method": "GET",
                                                 "Access-Control-Request-Headers": "authorization"})
    assert answer.headers["access-control-allow-origin"] == "http://localhost:4200"
    other = client.options("/expenses", headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "GET"})
    assert "access-control-allow-origin" not in other.headers


def test_cors_origins_come_from_the_environment(monkeypatch):
    import api

    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    assert api.allowed_origins() == ["http://localhost:4200"]
    monkeypatch.setenv("CORS_ORIGINS", " https://someone.github.io/ , http://localhost:4200,")
    assert api.allowed_origins() == ["https://someone.github.io", "http://localhost:4200"]


def test_cors_allows_changing_an_expense_from_the_website(client):
    answer = client.options("/expenses/1", headers={"Origin": "http://localhost:4200", "Access-Control-Request-Method": "PUT",
                                                   "Access-Control-Request-Headers": "authorization,content-type"})
    assert answer.status_code == 200 and "PUT" in answer.headers["access-control-allow-methods"]
