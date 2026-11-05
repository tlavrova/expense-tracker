"""The AI endpoint (Gemini is never called: ai_helper is replaced or has no key)."""

import ai_helper
from routers import ai


def test_suggest_category(client, sign_up, monkeypatch):
    monkeypatch.setattr(ai_helper, "suggest_category", lambda description: "transport")
    answer = client.post("/suggest-category", json={"description": "Uber to airport"}, headers=sign_up())
    assert answer.json() == {"category": "transport"}


def test_suggest_category_without_ai(client, sign_up):
    answer = client.post("/suggest-category", json={"description": "Uber"}, headers=sign_up())
    assert answer.status_code == 503 and answer.json() == {"detail": "GEMINI_API_KEY is not set."}


def test_each_account_gets_20_suggestions_an_hour(client, sign_up, monkeypatch):
    monkeypatch.setattr(ai_helper, "suggest_category", lambda description: "food")
    ana, bob = sign_up(), sign_up("bob@example.com", "bobs password")
    for _ in range(20):
        assert client.post("/suggest-category", json={"description": "Lunch"}, headers=ana).status_code == 200
    answer = client.post("/suggest-category", json={"description": "Lunch"}, headers=ana)
    assert answer.status_code == 429
    assert answer.json() == {"detail": "Too many AI suggestions. Try again in 60 minutes."}
    assert int(answer.headers["Retry-After"]) > 0
    assert client.post("/suggest-category", json={"description": "Lunch"}, headers=bob).status_code == 200  # counted per account


def test_failed_suggestions_count_too(client, sign_up):
    ai.suggestions_per_user.limit = 2  # the real limit is 20; the same rule, quicker to reach
    try:
        headers = sign_up()
        for _ in range(2):  # no GEMINI_API_KEY in the tests: 503, but Gemini would have been asked
            assert client.post("/suggest-category", json={"description": "Uber"}, headers=headers).status_code == 503
        assert client.post("/suggest-category", json={"description": "Uber"}, headers=headers).status_code == 429
    finally:
        ai.suggestions_per_user.limit = 20
