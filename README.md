# Expense Tracker

An app for recording daily expenses, viewing summaries by category and date, and saving data
between runs. When the category is left empty, AI (Google Gemini, free tier) suggests one from
the expense description.

A pet project to practise the Complete Python Bootcamp, one stage per course section. The Python
core starts as a command-line app (stages 1–8), then gets a REST API (FastAPI) and an
Angular frontend (stages 9–11). The Angular shell (10a) starts with mock data right after
stage 4, alongside the remaining Python stages. Finally it gets a login and goes online as a
website (stages 12–13).

```
=== Expense Tracker ===
1) Add expense   2) Show all   3) Summary   4) Filter
5) Month   6) Statistics   7) Delete   8) Quit
> 1
Description: Uber to airport
Amount: 32.50
Category (leave empty for AI suggestion):
🤖 Asking Gemini… (Ctrl+C to skip)
🤖 Suggested: transport — accept? (Y/n): y
Date (YYYY-MM-DD, empty for today):
Repeats (weekly/monthly/yearly, empty if not):
✅ Saved.
```

## Install

Backend (Python 3.10 or newer recommended; the Python 3.9 that comes with macOS is no longer
supported):

```bash
cd backend
python3.12 -m venv .venv      # any Python 3.10+; the virtual environment is git-ignored
source .venv/bin/activate
pip install -r requirements.txt
```

Frontend (from stage 10a; needs Node.js 22 or newer). The Angular CLI comes with the project,
so no global install is needed:

```bash
cd frontend
npm install
```

## AI key (Gemini free tier)

The AI suggestion uses the Google Gemini API's free tier. Create a free key in Google AI Studio
and put it in an environment variable; it is never stored in the code. Only the backend calls
Gemini, so the key never reaches the browser.

```bash
export GEMINI_API_KEY=...
export GEMINI_MODEL=...   # optional, default gemini-3.5-flash
```

To keep the key between terminal sessions, add the `export GEMINI_API_KEY=...` line to
`~/.zshrc` (outside the project, so it can never be committed). Online (stage 13), the key goes
into the hosting service's environment settings instead; the code reads it the same way.

Without a key, without internet, or when the free-tier limit is reached, the app falls back to
picking the category by hand. Free-tier answers usually take 1–10 seconds; Ctrl+C skips the
suggestion. The free tier also has a per-minute limit, so many suggestions in a row can hit it.

On the free tier, Google may use what is sent (the expense descriptions) to improve its
products, so don't put anything private in descriptions.

## Data (database)

Expenses are stored in a database through SQLModel. On your Mac that is the SQLite file
`backend/expenses.db`, created on first start; it is git-ignored, so your data never gets
committed. To use another database, set `DATABASE_URL`; online (stage 13) that will be a hosted
Postgres:

```bash
export DATABASE_URL=postgresql://user:password@host/dbname   # optional; default is expenses.db
export SQL_ECHO=1                                            # optional; print the SQL SQLModel sends
```

Upgrading from stage 7 or 8: on the first start, the expenses in `backend/expenses.json` are moved
into the database once, and the file is renamed to `expenses.json.imported` (keep it as a backup
or delete it). This only happens while the database is still empty, so nothing is imported twice.

## Run

Command-line app (stages 1–8):

```bash
cd backend
source .venv/bin/activate
python main.py
```

Web app, in two terminals (the frontend reads and saves everything through the API, so start
both):

```bash
cd backend && source .venv/bin/activate && uvicorn api:app --reload   # API on http://localhost:8000 (docs at /docs)
cd frontend && npm start                 # UI on http://localhost:4200
```

The API only accepts calls from `http://localhost:4200`, so keep the frontend on that port.
Where the frontend looks for the API is set in `frontend/src/environments/environment.ts`.

Frontend tests (Vitest; they use fake data, so the API doesn't need to run):

```bash
cd frontend && npm test
```

## API

FastAPI in `backend/api.py`; start it with `uvicorn api:app --reload` and try every endpoint at
http://localhost:8000/docs. It uses the same database and rules as the command-line app.

| Request | Does | Answer |
|---|---|---|
| `GET /expenses` | all expenses; optional `?category=food`, `?month=2026-11`, `?sort=amount` or `date` | list |
| `POST /expenses` | add one (amount, category, description, date, optional frequency) | `201` + the saved expense with its `id` |
| `DELETE /expenses/{id}` | delete one | `204`, or `404` |
| `GET /summary` | totals per category and overall | `{"totalsByCategory": {...}, "total": ...}` |
| `POST /suggest-category` | `{"description": "..."}` → Gemini's category | `{"category": "..."}`, or `503` when AI isn't available |

Errors always look like `{"detail": "a readable message"}` (`422` for invalid input).

## Stages

- [x] **1. Basics** — menu loop (add, show, quit); amount, category and description in a list; total spent
- [x] **2. Data structures** — each expense a dict (amount, category, description, date); totals per category; unique categories as a set
- [x] **3. Functions** — `add_expense()`, `show_all()`, `show_summary()`, `filter_by_category()`; sort by amount or date with `sorted()` + `lambda`
- [x] **4. OOP** — `Expense` with `__str__`; `ExpenseTracker` holding the list; `RecurringExpense(Expense)` with a frequency; classes live in `models.py`, the menu in `main.py`
- [x] **5. Errors and exceptions** — bad input never crashes; custom `InvalidAmountError` for zero or negative amounts
- [x] **6. Files and modules** — auto save/load `expenses.json` in `storage.py`; input helpers in `prompts.py`; `main.py` only has the screens and the menu
- [x] **7. Advanced Python** — `@log_action` decorator; generator for a chosen month; `datetime`, `defaultdict`/`Counter` for stats
- [x] **8. AI auto-categorization** — `ai_helper.suggest_category(description: str) -> str` with the Gemini API free tier via the `google-genai` package; key in `GEMINI_API_KEY`; only food, transport, housing, entertainment, shopping, health or other (anything else becomes other); accept or override; falls back to manual on errors and rate limits
- [x] **8a. Database storage** — `storage.py` switches from JSON to a database through SQLModel: SQLite (`expenses.db`) on your Mac, Postgres online, chosen by `DATABASE_URL`; one row per expense with an `id`, `GROUP BY` for totals; delete from the menu; one-time import of `expenses.json`
- [x] **9. REST API** — FastAPI app in `api.py` reusing `ExpenseTracker` and `storage`: list, add, delete, summary, filter, and suggest-category endpoints; CORS for the Angular dev server
- [x] **10a. Angular shell (mock data)** — can start right after stage 4: Angular app in `frontend/` with routing and layout; `Expense` interface; `ExpenseService` returning mock data; list page with total
- [x] **10. Angular: list and add** — switch `ExpenseService` to `HttpClient` against the API; add form with validation
- [x] **11. Angular: summary, filter and AI** — totals per category, filter by category and month, sort; AI suggestion in the add form (accept or override, manual fallback)
- [ ] **12. Login** — sign-up and login (hashed passwords, token) in FastAPI; each expense belongs to a user; Angular login page, interceptor and route guard
- [ ] **13. Deploy** — Angular on GitHub Pages (GitHub Actions), FastAPI on a free host, free hosted Postgres, Gemini key as a host secret; the site works from any device

## Structure

```
expense-tracker/
├── backend/
│   ├── main.py          # CLI start: logging, load data, menu loop
│   ├── screens.py       # one function per menu option
│   ├── prompts.py       # ask_text, ask_amount, ask_date, ask_month, ask_frequency
│   ├── decorators.py    # @log_action
│   ├── models.py        # Expense, RecurringExpense, ExpenseTracker
│   ├── storage.py       # database storage via SQLModel: add, delete, totals, JSON import
│   ├── ai_helper.py     # AI category suggestion (Gemini)
│   ├── api.py           # FastAPI app: CORS, error format, includes the routers
│   ├── schemas.py       # the API's JSON shapes (Pydantic)
│   ├── routers/
│   │   └── expenses.py  # /expenses, /summary, /suggest-category
│   ├── expenses.db      # local SQLite data (git-ignored; created on first start)
│   ├── expenses.log     # action log from @log_action (git-ignored)
│   └── requirements.txt # google-genai, fastapi, uvicorn, sqlmodel
├── frontend/            # Angular 22 app
│   └── src/
│       ├── environments/environment.ts  # apiUrl: where the API runs
│       ├── styles.css                   # colors, form fields, buttons and tables shared by all pages
│       └── app/
│           ├── app.ts / app.html   # layout: header + navigation
│           ├── app.routes.ts       # /expenses, /expenses/new, /summary
│           ├── core/
│           │   └── api-error.ts    # turns a failed API call into a sentence for the page
│           └── expenses/
│               ├── expense.model.ts    # Expense, NewExpense, Summary, filters; CATEGORIES, FREQUENCIES
│               ├── expense.service.ts  # the only data source: HttpClient calls to the API
│               ├── expense-list/       # list with filters (kept in the address), total and delete
│               ├── expense-filter-bar/ # category, month and sort fields above the list
│               ├── add-expense/        # add form with validation and the AI category suggestion
│               └── summary/            # totals per category with their share
└── README.md
```

## Later

Budget limits with warnings · charts in the Angular UI · unit tests (pytest, Angular tests) ·
more AI: natural-language input, monthly summary
