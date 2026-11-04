"""Suggest an expense category with the Google Gemini API (free tier).

Settings come from environment variables, never from the code:
  GEMINI_API_KEY  the key from Google AI Studio (required)
  GEMINI_MODEL    which model to use (optional, see DEFAULT_MODEL)

Anything that goes wrong (no key, no internet, rate limit, timeout, an API error) raises
AIUnavailableError with a short reason, so the caller can fall back to asking the user.
Nothing here reads input or prints, so the API (stage 9) can reuse it.
"""

from __future__ import annotations

import functools
import logging
import os
from typing import Any

from models import CATEGORIES

DEFAULT_MODEL = "gemini-3.5-flash"
TIMEOUT_SECONDS = 15

SYSTEM_INSTRUCTION = (
    "You sort personal expenses into categories. "
    "Reply with the single category that fits the expense description best."
)

logger = logging.getLogger("expense_tracker")


class AIUnavailableError(Exception):
    """The AI couldn't give a suggestion; the message says why, in words for the user."""


def normalize_category(answer: str) -> str:
    """Turn the model's answer into one of CATEGORIES; anything unexpected becomes "other"."""
    cleaned = answer.strip().strip("\"'.").lower()
    return cleaned if cleaned in CATEGORIES else "other"


def suggest_category(description: str) -> str:
    """Ask Gemini for the category of an expense description. Raises AIUnavailableError."""
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise AIUnavailableError("GEMINI_API_KEY is not set.")
    try:
        from google.genai import errors  # imported here so the app still runs without the package
    except ImportError:
        raise AIUnavailableError(
            "the google-genai package isn't installed (pip install -r requirements.txt)."
        ) from None

    model = os.environ.get("GEMINI_MODEL", "").strip() or DEFAULT_MODEL
    try:
        try:
            answer = _generate(api_key, model, description, minimal_thinking=True)
        except errors.ClientError as error:
            if error.code != 400:
                raise
            # Not every model accepts thinking_level=MINIMAL; try once more without it.
            answer = _generate(api_key, model, description, minimal_thinking=False)
    except errors.APIError as error:
        logger.warning("Gemini API error %s %s: %s", error.code, error.status, error.message)
        raise AIUnavailableError(_reason(error.code)) from error
    except Exception as error:  # network problems, timeouts
        logger.warning("Gemini request failed: %r", error)
        raise AIUnavailableError("couldn't reach Gemini (no internet, or it took too long).") from error
    return normalize_category(answer)


def _reason(code: int | None) -> str:
    if code == 429:
        return "the free-tier limit is reached; try again in a minute."
    if code in (401, 403):
        return "Gemini rejected the API key."
    if code == 404:
        return "the model in GEMINI_MODEL wasn't found."
    if code in (500, 502, 503, 504):
        return "Gemini is busy or not answering right now."
    return f"Gemini returned an error ({code})."


@functools.lru_cache(maxsize=1)
def _client(api_key: str) -> Any:
    from google import genai
    from google.genai import types

    return genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(
            timeout=TIMEOUT_SECONDS * 1000,  # milliseconds
            retry_options=types.HttpRetryOptions(attempts=1),  # no automatic retries
        ),
    )


def _generate(api_key: str, model: str, description: str, minimal_thinking: bool) -> str:
    from google.genai import types

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        # The answer must be exactly one of CATEGORIES.
        response_mime_type="text/x.enum",
        response_schema={"type": "STRING", "enum": list(CATEGORIES)},
        thinking_config=types.ThinkingConfig(thinking_level="MINIMAL") if minimal_thinking else None,
    )
    response = _client(api_key).models.generate_content(
        model=model,
        contents=f"Expense description: {description}",
        config=config,
    )
    return response.text or ""
