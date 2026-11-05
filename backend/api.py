"""REST API for the Angular frontend: the same data and rules as the command-line app.

Run it from backend/:  uvicorn api:app --reload   (docs at http://localhost:8000/docs)

This file creates the app and sets up what every endpoint shares: CORS, the startup step and
the error format. The endpoints live in routers/, the JSON shapes in schemas.py.

Login (stage 12): routers/auth.py signs up and logs in; every expense endpoint needs the token
it returns and sees only that user's expenses. JWT_SECRET must be set, or the API won't start.

Every request reads the database through storage.py; nothing is kept in memory between
requests. The amount, date and frequency rules live in models.py, so the API and the CLI accept
exactly the same expenses. The Gemini key stays here on the server and never reaches the browser.
Every error answer has the same shape, {"detail": "a readable message"}, so the frontend can show it.
uvicorn logs each request, so the endpoints don't use @log_action.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import database
import json_import
import security
import storage
from routers import ai, auth, budgets, expenses, reports

# Where the Angular dev server runs (npm start). Online, CORS_ORIGINS names the deployed site.
DEV_ORIGIN = "http://localhost:4200"


def allowed_origins() -> list[str]:
    """The sites whose pages may call the API: CORS_ORIGINS (comma-separated), or the dev server."""
    origins = [o.strip().rstrip("/") for o in os.environ.get("CORS_ORIGINS", "").split(",")]
    return [o for o in origins if o] or [DEV_ORIGIN]


@asynccontextmanager
async def lifespan(app: FastAPI):
    security.jwt_secret()  # stop right away with a clear message if JWT_SECRET is missing
    # Connect and run the migrations now, not on the first request: if one fails, the API doesn't
    # start, so the host's deploy fails and keeps the previous version running.
    database.get_engine()
    json_import.import_json()  # the same one-time move of expenses.json as the CLI
    yield


app = FastAPI(title="Expense Tracker API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins(),
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.exception_handler(storage.StorageError)
def storage_error(request: Request, error: storage.StorageError) -> JSONResponse:
    return JSONResponse(status_code=500, content={"detail": str(error)})


@app.exception_handler(RequestValidationError)
def validation_error(request: Request, error: RequestValidationError) -> JSONResponse:
    """FastAPI's own checks (types, query patterns) as one readable string, like our own errors."""
    messages = [f"{problem['loc'][-1]}: {problem['msg']}" for problem in error.errors()]
    return JSONResponse(status_code=422, content={"detail": "; ".join(messages)})


app.include_router(auth.router)
app.include_router(expenses.router)
app.include_router(reports.router)
app.include_router(budgets.router)
app.include_router(ai.router)
