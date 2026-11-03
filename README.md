# Expense Tracker

An app for recording daily expenses, viewing summaries by category and date, and saving data
between runs. When the category is left empty, AI (Claude) suggests one from the expense
description.

A pet project to practise the Complete Python Bootcamp, one stage per course section. The Python
core starts as a command-line app (stages 1–8), then gets a REST API (FastAPI) and an
Angular frontend (stages 9–11). The Angular shell (10a) starts with mock data right after
stage 4, alongside the remaining Python stages.

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

Backend (Python 3):

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Frontend (from stage 10a; needs Node.js 22 or newer). The Angular CLI comes with the project,
so no global install is needed:

```bash
cd frontend
npm install
```

## API key

The AI suggestion reads the key from the `ANTHROPIC_API_KEY` environment variable; it is never
stored in the code. Only the backend calls Claude, so the key never reaches the browser.

```bash
export ANTHROPIC_API_KEY=...
```

Without a key, or without internet, the app falls back to picking the category by hand.

## Run

Command-line app (stages 1–8):

```bash
cd backend
python3 main.py
```

Frontend only, with mock data (stage 10a):

```bash
cd frontend && npm start                 # UI on http://localhost:4200
cd frontend && npm test                  # unit tests (Vitest)
```

Web app (stages 9–11), in two terminals:

```bash
cd backend && uvicorn api:app --reload   # API on http://localhost:8000 (docs at /docs)
cd frontend && npm start                 # UI on http://localhost:4200
```

## Stages

- [x] **1. Basics** — menu loop (add, show, quit); amount, category and description in a list; total spent
- [x] **2. Data structures** — each expense a dict (amount, category, description, date); totals per category; unique categories as a set
- [x] **3. Functions** — `add_expense()`, `show_all()`, `show_summary()`, `filter_by_category()`; sort by amount or date with `sorted()` + `lambda`
- [x] **4. OOP** — `Expense` with `__str__`; `ExpenseTracker` holding the list; `RecurringExpense(Expense)` with a frequency; classes live in `models.py`, the menu in `main.py`
- [x] **5. Errors and exceptions** — bad input never crashes; custom `InvalidAmountError` for zero or negative amounts
- [x] **6. Files and modules** — auto save/load `expenses.json` in `storage.py`; input helpers in `prompts.py`; `main.py` only has the screens and the menu
- [x] **7. Advanced Python** — `@log_action` decorator; generator for a chosen month; `datetime`, `defaultdict`/`Counter` for stats
- [ ] **8. AI auto-categorization** — `ai_helper.suggest_category(description: str) -> str` with Claude (`claude-haiku-5-5`) via the `anthropic` SDK; only food, transport, housing, entertainment, shopping, health or other (anything else becomes other); accept or override; falls back to manual on errors
- [ ] **8a. SQLite storage** — `storage.py` switches from JSON to the built-in `sqlite3` with `expenses.db`: one row per expense with an `id`, parameterized queries, `GROUP BY` for totals; delete from the menu; one-time import of `expenses.json`
- [ ] **9. REST API** — FastAPI app in `api.py` reusing `ExpenseTracker` and `storage`: list, add, delete, summary, filter, and suggest-category endpoints; CORS for the Angular dev server
- [x] **10a. Angular shell (mock data)** — can start right after stage 4: Angular app in `frontend/` with routing and layout; `Expense` interface; `ExpenseService` returning mock data; list page with total
- [ ] **10. Angular: list and add** — switch `ExpenseService` to `HttpClient` against the API; add form with validation
- [ ] **11. Angular: summary, filter and AI** — totals per category, filter by category and month, sort; AI suggestion in the add form (accept or override, manual fallback)

## Structure

```
expense-tracker/
├── backend/
│   ├── main.py          # CLI start: logging, load data, menu loop
│   ├── screens.py       # one function per menu option
│   ├── prompts.py       # ask_text, ask_amount, ask_date, ask_month, ask_frequency
│   ├── decorators.py    # @log_action
│   ├── models.py        # Expense, RecurringExpense, ExpenseTracker
│   ├── storage.py       # SQLite storage (JSON until stage 8a)
│   ├── ai_helper.py     # AI category suggestion
│   ├── api.py           # FastAPI REST API for the frontend
│   ├── expenses.db      # data (git-ignored; expenses.json before stage 8a)
│   ├── expenses.log     # action log from @log_action (git-ignored)
│   └── requirements.txt # anthropic, fastapi, uvicorn
├── frontend/            # Angular 22 app
│   └── src/app/
│       ├── expense.model.ts    # Expense, NewExpense, Summary types
│       ├── expense.service.ts  # the only data source (mock now, HttpClient from stage 10)
│       ├── mock-expenses.ts    # sample data until the API exists
│       ├── app.ts / app.html   # layout: header + navigation
│       ├── app.routes.ts       # /expenses, /expenses/new, /summary
│       ├── expense-list/       # list page with total
│       ├── add-expense/        # placeholder until stage 10
│       └── summary/            # placeholder until stage 11
└── README.md
```

## Later

Budget limits with warnings · charts in the Angular UI · an ORM (SQLModel/SQLAlchemy) instead of hand-written SQL · unit tests
(pytest, Angular tests) · more AI: natural-language input, monthly summary
