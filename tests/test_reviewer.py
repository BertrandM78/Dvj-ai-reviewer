from unittest.mock import patch

from src.reviewer import review


FAKE_RULES = [
    {
        "id": "RULE_DET",
        "engine": "DETERMINISTIC",
    },
    {
        "id": "RULE_LLM",
        "engine": "LLM",
    },
    {
        "id": "RULE_RAW",
        "engine": "RAW_TEXT_LLM",
    },
]


@patch("src.reviewer.load_rules")
@patch("src.reviewer.run_deterministic_rules")
@patch("src.reviewer.run_llm_rules")
def test_review_runs_each_active_engine_once(
    mock_llm,
    mock_deterministic,
    mock_load_rules,
):
    mock_load_rules.return_value = FAKE_RULES

    mock_deterministic.return_value = [
        {
            "rule_id": "RULE_DET",
            "status": "COMPLIANT",
        }
    ]

    mock_llm.return_value = [
        {
            "rule_id": "RULE_LLM",
            "status": "COMPLIANT",
        }
    ]

    results = review(
        {
            "metadata": {},
        }
    )

    assert len(results) == 2

    assert [
        result["rule_id"]
        for result in results
    ] == [
        "RULE_DET",
        "RULE_LLM",
    ]

    mock_deterministic.assert_called_once()
    mock_llm.assert_called_once()