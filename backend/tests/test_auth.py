"""Accounts, login tokens and the rate limits on logging in."""

import sqlite3
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi.testclient import TestClient

from routers import auth
from tests.conftest import TEST_SECRET


def login(client, email="ana@example.com", password="correct horse", headers=None):
    return client.post("/auth/login", data={"username": email, "password": password}, headers=headers)


def test_sign_up_log_in_and_me(client, sign_up):
    headers = sign_up(" Ana@Example.com ")
    assert client.get("/auth/me", headers=headers).json()["email"] == "ana@example.com"
    answer = login(client, "ANA@example.com")
    assert answer.status_code == 200 and answer.json()["token_type"] == "bearer"


@pytest.mark.parametrize(
    ("body", "message"),
    [
        ({"email": "not-an-email", "password": "long enough"}, "email: value is not a valid email"),
        ({"email": "ana@example.com", "password": "short"}, "password: String should have at least 8"),
    ],
)
def test_sign_up_checks_email_and_password(client, body, message):
    answer = client.post("/auth/signup", json=body)
    assert answer.status_code == 422 and answer.json()["detail"].startswith(message)


def test_one_account_per_email_whatever_the_case(client, sign_up):
    sign_up("ana@example.com")
    answer = client.post("/auth/signup", json={"email": "ANA@example.com", "password": "another one"})
    assert answer.status_code == 409


def test_wrong_password_and_unknown_email_look_the_same(client, sign_up):
    sign_up()
    wrong = login(client, password="wrong password")
    unknown = login(client, email="nobody@example.com")
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json() == {"detail": "Wrong email or password."}


def test_only_a_hash_of_the_password_is_stored(client, sign_up, tmp_path):
    sign_up(password="correct horse")
    rows = sqlite3.connect(tmp_path / "test.db").execute("select * from users").fetchall()
    assert "correct horse" not in str(rows)
    assert rows[0][2].startswith("$argon2id$")


def token(sub="1", expires_in=timedelta(hours=1), secret=TEST_SECRET, **extra):
    claims = {"sub": sub, **extra}
    if expires_in is not None:
        claims["exp"] = datetime.now(timezone.utc) + expires_in
    return jwt.encode(claims, secret, algorithm="HS256")


@pytest.mark.parametrize(
    ("bad_token", "message"),
    [
        (token(expires_in=timedelta(minutes=-1)), "Your login has expired. Please log in again."),
        (token(secret="someone-elses-secret-0123456789-abcdef"), "Please log in."),
        (token(expires_in=None), "Please log in."),
        (token(sub="not-a-number"), "Please log in."),
        (token(sub="999"), "Please log in."),  # a user that doesn't exist (any more)
        ("garbage", "Please log in."),
    ],
)
def test_bad_tokens_are_refused(client, sign_up, bad_token, message):
    sign_up()
    answer = client.get("/auth/me", headers={"Authorization": f"Bearer {bad_token}"})
    assert answer.status_code == 401
    assert answer.json() == {"detail": message}


def test_no_token_at_all(client):
    answer = client.get("/expenses")
    assert answer.status_code == 401 and answer.json() == {"detail": "Please log in."}


def test_tokens_last_seven_days(client, sign_up):
    sign_up()
    claims = jwt.decode(login(client).json()["access_token"], TEST_SECRET, algorithms=["HS256"])
    assert claims["exp"] - claims["iat"] == 7 * 24 * 3600


@pytest.mark.parametrize("secret", ["", "too-short"])
def test_the_api_does_not_start_without_a_proper_secret(monkeypatch, secret):
    import api
    import security

    monkeypatch.setenv("JWT_SECRET", secret)
    with pytest.raises(security.MissingSecretError):
        with TestClient(api.app):
            pass


def test_five_failed_logins_lock_that_email_from_that_address(client, sign_up):
    sign_up()
    for _ in range(5):
        assert login(client, password="wrong password").status_code == 401
    locked = login(client)  # even the right password: guessing stops before the password check
    assert locked.status_code == 429
    assert locked.json()["detail"] == "Too many attempts. Try again in 15 minutes."
    assert int(locked.headers["Retry-After"]) > 0
    sign_up("bob@example.com", "bobs password")
    assert login(client, "bob@example.com", "bobs password").status_code == 200  # other emails still work


def test_a_successful_login_starts_the_count_over(client, sign_up):
    sign_up()
    for _ in range(4):
        login(client, password="wrong password")
    assert login(client).status_code == 200
    for _ in range(4):
        assert login(client, password="wrong password").status_code == 401


def test_too_many_attempts_from_one_address(client):
    auth.attempts_per_ip.limit = 3  # the real limit is 30; the same rule, quicker to reach
    try:
        for n in range(3):
            client.post("/auth/signup", json={"email": f"user{n}@example.com", "password": "long enough"})
        assert login(client, "user0@example.com", "long enough").status_code == 429
        assert client.post("/auth/signup", json={"email": "x@example.com", "password": "long enough"}).status_code == 429
    finally:
        auth.attempts_per_ip.limit = 30


def test_the_address_comes_from_client_ip_header_when_set(client, sign_up, monkeypatch):
    """Online: the header the host's proxy sets counts, not X-Forwarded-For or the connection."""
    monkeypatch.setenv("CLIENT_IP_HEADER", "True-Client-IP")
    sign_up()
    for n in range(5):  # a made-up X-Forwarded-For each time doesn't reset the count
        made_up = {"True-Client-IP": "203.0.113.7", "X-Forwarded-For": f"198.51.100.{n}"}
        assert login(client, password="wrong password", headers=made_up).status_code == 401
    assert login(client, headers={"True-Client-IP": "203.0.113.7"}).status_code == 429
    assert login(client, headers={"True-Client-IP": "203.0.113.8"}).status_code == 200  # another visitor
