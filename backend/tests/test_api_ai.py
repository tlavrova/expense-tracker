"""The AI endpoint (Gemini is never called: ai_helper is replaced or has no key)."""

import ai_helper


def test_suggest_category(client, sign_up, monkeypatch):
    monkeypatch.setattr(ai_helper, "suggest_category", lambda description: "transport")
    answer = client.post("/suggest-category", json={"description": "Uber to airport"}, headers=sign_up())
    assert answer.json() == {"category": "transport"}


def test_suggest_category_without_ai(client, sign_up):
    answer = client.post("/suggest-category", json={"description": "Uber"}, headers=sign_up())
    assert answer.status_code == 503 and answer.json() == {"detail": "GEMINI_API_KEY is not set."}
