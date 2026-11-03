"""Ask the user for one value at a time, repeating until the answer is valid."""

from __future__ import annotations

from datetime import date, datetime

from models import FREQUENCIES, InvalidAmountError, parse_date, validate_amount


def ask_text(prompt: str) -> str:
    """Ask until the answer is not empty."""
    while True:
        answer = input(prompt).strip()
        if answer:
            return answer
        print("⚠️  This can't be empty.")


def ask_amount() -> float:
    """Ask until the answer is a number greater than zero."""
    while True:
        answer = input("Amount: ").strip().replace(",", ".")
        try:
            return validate_amount(float(answer))
        except InvalidAmountError:
            print("⚠️  The amount must be greater than zero.")
        except ValueError:
            print("⚠️  Please enter a number, for example 12.50.")


def ask_date() -> date:
    """Ask until the answer is a real YYYY-MM-DD date; empty means today."""
    while True:
        answer = input("Date (YYYY-MM-DD, empty for today): ").strip()
        if not answer:
            return date.today()
        try:
            return parse_date(answer)
        except ValueError:
            print("⚠️  Please enter a real date as YYYY-MM-DD, for example 2026-11-03.")


def ask_month() -> tuple[int, int]:
    """Ask until the answer is a month as YYYY-MM; empty means this month. Returns (year, month)."""
    while True:
        answer = input("Month (YYYY-MM, empty for this month): ").strip()
        if not answer:
            today = date.today()
            return today.year, today.month
        try:
            parsed = datetime.strptime(answer, "%Y-%m")
        except ValueError:
            print("⚠️  Please enter a month as YYYY-MM, for example 2026-11.")
            continue
        return parsed.year, parsed.month


def ask_frequency() -> str:
    """Ask until the answer is a known frequency or empty (not recurring)."""
    options = "/".join(FREQUENCIES)
    while True:
        answer = input(f"Repeats ({options}, empty if not): ").strip().lower()
        if not answer or answer in FREQUENCIES:
            return answer
        print(f"⚠️  Please choose {options}, or leave it empty.")
