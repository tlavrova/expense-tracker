"""The command-line screens, with typed answers given in advance."""

import builtins

import prompts
import screens
import storage
from models import Expense, ExpenseTracker


def answers(monkeypatch, *typed):
    queue = iter(typed)
    monkeypatch.setattr(builtins, "input", lambda prompt="": next(queue))


def test_amounts_are_asked_again_until_valid(monkeypatch, capsys):
    answers(monkeypatch, "abc", "0", "12,50")
    assert prompts.ask_amount() == 12.5
    printed = capsys.readouterr().out
    assert "Please enter a number" in printed and "greater than zero" in printed


def test_adding_an_expense_saves_it_as_the_clis_own(monkeypatch):
    tracker = ExpenseTracker()
    answers(monkeypatch, "Coffee", "3.50", "food", "2026-11-04", "")
    screens.add_expense(tracker)
    assert [e.description for e in storage.load(owner=storage.LOCAL).expenses] == ["Coffee"]
    assert len(tracker) == 1


def test_screens_say_so_when_there_are_no_expenses(capsys):
    screens.show_summary(ExpenseTracker())
    assert "No expenses yet." in capsys.readouterr().out


def test_delete_asks_first(monkeypatch):
    expense = storage.add(Expense(3.5, "food", "Coffee", "2026-11-04"), owner=storage.LOCAL)
    tracker = ExpenseTracker([expense])
    answers(monkeypatch, "1", "n")
    screens.delete_expense(tracker)
    assert len(storage.load(owner=storage.LOCAL)) == 1
    answers(monkeypatch, "1", "y")
    screens.delete_expense(tracker)
    assert len(storage.load(owner=storage.LOCAL)) == 0 and len(tracker) == 0
