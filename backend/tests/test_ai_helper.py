"""The AI suggestion without calling Gemini: answers are cleaned, failures explained."""

import pytest

import ai_helper


@pytest.mark.parametrize(("answer", "category"), [("Transport", "transport"), (' "food." ', "food"), ("travel", "other")])
def test_answers_become_one_of_the_categories(answer, category):
    assert ai_helper.normalize_category(answer) == category


def test_no_key_means_no_suggestion():
    with pytest.raises(ai_helper.AIUnavailableError, match="GEMINI_API_KEY is not set"):
        ai_helper.suggest_category("Uber")


@pytest.mark.parametrize(
    ("code", "reason"),
    [(429, "free-tier limit"), (401, "rejected the API key"), (404, "wasn't found"), (503, "busy"), (418, "(418)")],
)
def test_api_errors_are_explained(code, reason):
    assert reason in ai_helper._reason(code)
