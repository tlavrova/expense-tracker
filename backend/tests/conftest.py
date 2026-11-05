"""Shared setup for the backend tests.

Every test gets its own empty database in a temporary folder, a test JWT_SECRET, no Gemini key and
fresh rate limits, so tests never touch backend/expenses.db, backend/expenses.json, each other, or
the internet.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator

import pytest
from fastapi.testclient import TestClient

import database
import json_import
from routers import ai, auth

TEST_SECRET = "test-secret-for-pytest-only-0123456789"


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch) -> Iterator[None]:
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'test.db'}")
    monkeypatch.setenv("JWT_SECRET", TEST_SECRET)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("SQL_ECHO", raising=False)
    monkeypatch.delenv("CLIENT_IP_HEADER", raising=False)
    monkeypatch.setattr(json_import, "JSON_PATH", tmp_path / "expenses.json")
    database.get_engine.cache_clear()
    auth.failed_logins.reset()
    auth.attempts_per_ip.reset()
    ai.suggestions_per_user.reset()
    yield
    database.get_engine.cache_clear()


@pytest.fixture
def client() -> Iterator[TestClient]:
    """The API, started as uvicorn would (the lifespan runs)."""
    import api

    with TestClient(api.app) as test_client:
        yield test_client


@pytest.fixture
def sign_up(client: TestClient) -> Callable[..., dict[str, str]]:
    """Create an account; returns the headers to send as that user."""

    def make(email: str = "ana@example.com", password: str = "correct horse") -> dict[str, str]:
        answer = client.post("/auth/signup", json={"email": email, "password": password})
        assert answer.status_code == 201, answer.text
        return {"Authorization": f"Bearer {answer.json()['access_token']}"}

    return make
