import pytest

from src.rules.aggregator import aggregate_results


RULES = [
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


def test_aggregator_combines_results_in_rule_order():
    deterministic_results = [
        {
            "rule_id": "RULE_DET",
            "status": "COMPLIANT",
        }
    ]

    llm_results = [
        {
            "rule_id": "RULE_LLM",
            "status": "NON_COMPLIANT",
        }
    ]

    results = aggregate_results(
        deterministic_results,
        llm_results,
        rules=RULES,
    )

    assert [
        result["rule_id"]
        for result in results
    ] == [
        "RULE_DET",
        "RULE_LLM",
    ]


def test_aggregator_ignores_inactive_raw_text_rules():
    deterministic_results = [
        {
            "rule_id": "RULE_DET",
            "status": "COMPLIANT",
        }
    ]

    llm_results = [
        {
            "rule_id": "RULE_LLM",
            "status": "COMPLIANT",
        }
    ]

    results = aggregate_results(
        deterministic_results,
        llm_results,
        rules=RULES,
    )

    ids = {
        result["rule_id"]
        for result in results
    }

    assert "RULE_RAW" not in ids


def test_aggregator_rejects_missing_result():
    deterministic_results = [
        {
            "rule_id": "RULE_DET",
            "status": "COMPLIANT",
        }
    ]

    with pytest.raises(
        ValueError,
        match="Missing rule results",
    ):
        aggregate_results(
            deterministic_results,
            [],
            rules=RULES,
        )


def test_aggregator_rejects_duplicate_inside_engine():
    deterministic_results = [
        {
            "rule_id": "RULE_DET",
            "status": "COMPLIANT",
        },
        {
            "rule_id": "RULE_DET",
            "status": "NON_COMPLIANT",
        },
    ]

    llm_results = [
        {
            "rule_id": "RULE_LLM",
            "status": "COMPLIANT",
        }
    ]

    with pytest.raises(
        ValueError,
        match="Duplicate DETERMINISTIC",
    ):
        aggregate_results(
            deterministic_results,
            llm_results,
            rules=RULES,
        )


def test_aggregator_rejects_wrong_engine_ownership():
    deterministic_results = [
        {
            "rule_id": "RULE_LLM",
            "status": "COMPLIANT",
        }
    ]

    llm_results = [
        {
            "rule_id": "RULE_DET",
            "status": "COMPLIANT",
        }
    ]

    with pytest.raises(
        ValueError,
        match="does not own",
    ):
        aggregate_results(
            deterministic_results,
            llm_results,
            rules=RULES,
        )