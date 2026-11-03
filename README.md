# Expense Tracker

A command-line app for recording daily expenses, viewing summaries by category and date, and
saving data between runs. When the category is left empty, AI (Claude) suggests one from the
expense description.

A pet project to practise the Complete Python Bootcamp, one stage per course section.

```
=== Expense Tracker ===
1) Add expense   2) Show all   3) Summary   4) Filter   5) Quit
> 1
Description: Uber to airport
Amount: 32.50
Category (leave empty for AI suggestion):
🤖 Suggested: transport — accept? (y/n): y
✅ Saved.
```

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## API key

The AI suggestion reads the key from the `ANTHROPIC_API_KEY` environment variable; it is never
stored in the code.

```bash
export ANTHROPIC_API_KEY=...
```

Without a key, or without internet, the app falls back to picking the category by hand.

## Run

```bash
python3 main.py
```

## Stages

- [ ] **1. Basics** — menu loop (add, show, quit); amount, category and description in a list; total spent
- [ ] **2. Data structures** — each expense a dict (amount, category, description, date); totals per category; unique categories as a set
- [ ] **3. Functions** — `add_expense()`, `show_all()`, `show_summary()`, `filter_by_category()`; sort by amount or date with `sorted()` + `lambda`
- [ ] **4. OOP** — `Expense` with `__str__`; `ExpenseTracker` holding the list; `RecurringExpense(Expense)` with a frequency
- [ ] **5. Errors and exceptions** — bad input never crashes; custom `InvalidAmountError` for zero or negative amounts
- [ ] **6. Files and modules** — auto save/load `expenses.json`; split into `models.py`, `storage.py`, `main.py`
- [ ] **7. Advanced Python** — `@log_action` decorator; generator for a chosen month; `datetime`, `defaultdict`/`Counter` for stats
- [ ] **8. AI auto-categorization** — `ai_helper.suggest_category(description: str) -> str` with Claude (`claude-haiku-5-5`) via the `anthropic` SDK; only food, transport, housing, entertainment, shopping, health or other (anything else becomes other); accept or override; falls back to manual on errors

## Structure

```
expense-tracker/
├── main.py          # menu + user interaction
├── models.py        # Expense, RecurringExpense, ExpenseTracker
├── storage.py       # load/save JSON
├── ai_helper.py     # AI category suggestion
├── expenses.json    # data (git-ignored)
├── requirements.txt # anthropic
└── README.md
```

## Later

Budget limits with warnings · charts (matplotlib) · web interface (Streamlit/Flask) · SQLite
instead of JSON · unit tests (pytest) · more AI: natural-language input, monthly summary
