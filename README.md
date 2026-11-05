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

The tables are created and updated by Alembic migrations (`backend/migrations/`). They run by
themselves when the app starts, so an older `expenses.db` is upgraded automatically; its
expenses stay the command-line app's own. After changing a table class in `database.py`, draft
the next migration with `cd backend && alembic revision --autogenerate -m "what changed"`.

## Login (website)

On the website, everyone has their own account and sees only their own expenses. Passwords are
stored only as argon2 hashes. After login the browser gets a token, signed with a secret that the
API reads from `JWT_SECRET`; the API won't start without it. Make a random one once and keep it
in `~/.zshrc` (outside the project, so it can never be committed), next to the Gemini key:

```bash
echo "export JWT_SECRET=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')" >> ~/.zshrc
source ~/.zshrc
```

Changing the secret logs everyone out. Online (stage 13) the secret goes into the hosting
service's settings instead. The command-line app doesn't need it: it stays a local tool with its
own expenses, separate from the website accounts.

Password guessing is slowed down: after 5 wrong passwords for one email from one address, or 30
login and sign-up attempts from one address, within 15 minutes, the API answers "Too many
attempts. Try again in N minutes."

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

The API needs `JWT_SECRET` (see "Login" above). Open http://localhost:4200, create an account,
and you're logged in; "Log out" is in the header. A login lasts 7 days.

The API only accepts calls from `http://localhost:4200` (unless `CORS_ORIGINS` says otherwise,
see "Online settings"), so keep the frontend on that port. Where the frontend looks for the API is
set in `frontend/src/environments/environment.ts` (`npm start`) and `environment.prod.ts`
(`ng build`, the deployed site).

## Online settings

Locally none of these are needed. On the backend host they are set in its environment settings,
never in the repo:

| Variable | Online value |
|---|---|
| `DATABASE_URL` | the hosted Postgres address (`postgres://` or `postgresql://`; the API adds the psycopg driver) |
| `JWT_SECRET` | a random secret, made as in "Login" above |
| `GEMINI_API_KEY`, `GEMINI_MODEL` | as in "AI key" above |
| `CORS_ORIGINS` | the website's address, e.g. `https://<user>.github.io` (comma-separated for several) |
| `FORWARDED_ALLOW_IPS` | the address range of the host's proxy, so the login limits see each visitor's real address |

Start command: `uvicorn api:app --host 0.0.0.0 --port $PORT` (uvicorn reads
`FORWARDED_ALLOW_IPS` by itself). Don't set it to `*`: uvicorn would then believe whatever address
a visitor writes into the `X-Forwarded-For` header, and the login limits could be dodged.

Every pull request and push to `main` runs the backend and frontend tests on GitHub Actions
(`.github/workflows/tests.yml`).

## Tests

Neither needs the servers running, a Gemini key or internet: the backend tests use a temporary
database each, the frontend tests fake the API.

```bash
cd backend && source .venv/bin/activate
pip install -r requirements-dev.txt      # once: pytest and httpx2 (only for testing)
pytest                                   # backend: models, database, migrations, API, login, CLI

cd frontend && npm test -- --watch=false # frontend (Vitest)
```

## API

FastAPI in `backend/api.py`; start it with `uvicorn api:app --reload` and try every endpoint at
http://localhost:8000/docs (sign up there, then use "Authorize" with your email and password). It
uses the same database and rules as the command-line app.

| Request | Does | Answer |
|---|---|---|
| `POST /auth/signup` | `{"email": "...", "password": "..."}` (8+ characters); creates an account and logs in | `201` + `{"access_token": "...", "token_type": "bearer"}`, or `409` if the email has an account |
| `POST /auth/login` | form fields `username` (the email) and `password` | the same token, or `401` |
| `GET /auth/me` | who is logged in | `{"id": 1, "email": "..."}` |
| `GET /expenses` | your expenses; optional `?category=food`, `?month=2026-11`, `?sort=amount` or `date` | list |
| `POST /expenses` | add one (amount, category, description, date, optional frequency) | `201` + the saved expense with its `id` |
| `DELETE /expenses/{id}` | delete one | `204`, or `404` |
| `GET /summary` | totals per category and overall | `{"totalsByCategory": {...}, "total": ...}` |
| `POST /suggest-category` | `{"description": "..."}` → Gemini's category | `{"category": "..."}`, or `503` when AI isn't available |

Everything except sign-up and login needs the header `Authorization: Bearer <access_token>`;
without a valid one the answer is `401`. Another account's expense answers `404`, as if it didn't
exist. Errors always look like `{"detail": "a readable message"}` (`422` for invalid input).

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
- [x] **12. Login** — sign-up and login (hashed passwords, token) in FastAPI; each expense belongs to a user; Angular login page, interceptor and route guard
- [ ] **13. Deploy** — Angular on GitHub Pages (GitHub Actions), FastAPI on a free host, free hosted Postgres, Gemini key as a host secret; the site works from any device

## Structure

```
expense-tracker/
├── .github/workflows/tests.yml  # runs both test suites on every pull request
├── backend/
│   ├── main.py          # CLI start: logging, load data, menu loop
│   ├── screens.py       # one function per menu option
│   ├── prompts.py       # ask_text, ask_amount, ask_date, ask_month, ask_frequency
│   ├── decorators.py    # @log_action
│   ├── models.py        # Expense, RecurringExpense, ExpenseTracker
│   ├── database.py      # database connection (DATABASE_URL, SQL_ECHO), table classes, migrations
│   ├── storage.py       # expense queries for one owner (the CLI, or one account): list, add, delete, totals
│   ├── users.py         # accounts: create, find by email or id
│   ├── security.py      # password hashing, login tokens (JWT_SECRET), the logged-in user
│   ├── rate_limit.py    # "at most N times in M minutes", for login and sign-up attempts
│   ├── alembic.ini      # Alembic settings (database migrations)
│   ├── migrations/      # migration scripts: 0001 expenses table, 0002 users + expenses.user_id
│   ├── json_import.py   # one-time move of the old expenses.json into the database
│   ├── ai_helper.py     # AI category suggestion (Gemini)
│   ├── api.py           # FastAPI app: CORS, error format, includes the routers
│   ├── schemas.py       # the API's JSON shapes (Pydantic)
│   ├── routers/
│   │   ├── auth.py      # /auth/signup, /auth/login, /auth/me
│   │   └── expenses.py  # /expenses, /summary, /suggest-category (login required)
│   ├── expenses.db      # local SQLite data (git-ignored; created on first start)
│   ├── expenses.log     # action log from @log_action (git-ignored)
│   ├── tests/           # pytest: one temporary database per test, Gemini never called
│   ├── pytest.ini       # where the tests are
│   ├── requirements.txt # google-genai, fastapi, uvicorn, sqlmodel, alembic, pwdlib, PyJWT, psycopg, …
│   └── requirements-dev.txt # + pytest and httpx2, for the tests
├── frontend/            # Angular 22 app
│   └── src/
│       ├── environments/environment.ts  # apiUrl: where the API runs (environment.prod.ts online)
│       ├── styles.css                   # colors, form fields, buttons and tables shared by all pages
│       └── app/
│           ├── app.ts / app.html   # layout: header + navigation
│           ├── app.routes.ts       # /login, /signup; /expenses, /expenses/new, /summary need a login
│           ├── auth/
│           │   ├── auth.service.ts # who is logged in; log in, sign up, log out
│           │   ├── token.ts        # keeping the token between visits (localStorage), reading its expiry
│           │   ├── auth.guards.ts  # logged out → login page (and back afterwards); logged in → past it
│           │   └── auth-page/      # the login and sign-up page (one form, two modes)
│           ├── core/
│           │   ├── api-error.ts        # turns a failed API call into a sentence for the page
│           │   └── auth.interceptor.ts # adds the token to API calls only; a 401 logs out
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

Budget limits with warnings · charts in the Angular UI · editing an expense ·
more AI: natural-language input, monthly summary
