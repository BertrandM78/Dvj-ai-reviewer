from src.rules.loader import load_rules
from src.rules.deterministic import run_deterministic_rules


def run(document: dict) -> dict:
    results = run_deterministic_rules(
        normalized_document={"document": document},
        rules=load_rules(),
    )

    return {
        result["rule_id"]: result
        for result in results
    }


def test_project_start_date_weekend():
    results = run({
        "planning": {
            "project_start_date": "2026-09-20"
        }
    })

    assert results["RULE_019"]["status"] == "NON_COMPLIANT"


def test_project_start_date_weekday():
    results = run({
        "planning": {
            "project_start_date": "2026-09-21"
        }
    })

    assert results["RULE_019"]["status"] == "COMPLIANT"


def test_project_management_ratio_too_low():
    results = run({
        "budget": {
            "project_management_ht": 900,
            "total_ht": 12000
        }
    })

    assert results["RULE_022"]["status"] == "NON_COMPLIANT"


def test_project_manager_experience():
    results = run({
        "budget": {
            "total_ht": 12000
        },
        "team": {
            "project_manager": {
                "name": "Test CDP",
                "mission_count": 4,
                "project_management_weeks": 30
            }
        }
    })

    assert results["RULE_028"]["status"] == "COMPLIANT"


def test_project_manager_rule_not_applicable():
    results = run({
        "budget": {
            "total_ht": 9000
        }
    })

    assert results["RULE_028"]["status"] == "NOT_APPLICABLE"


def test_methodology_minimum_steps():
    results = run({
        "methodology": {
            "phases": [
                {
                    "number": 1,
                    "title": "Cadrage",
                    "steps": [
                        "Étape 1",
                        "Étape 2"
                    ]
                }
            ]
        }
    })

    assert results["RULE_009"]["status"] == "NON_COMPLIANT"


def test_phase_required_information():
    results = run({
        "methodology": {
            "phases": [
                {
                    "number": 1,
                    "title": "Cadrage",
                    "duration_weeks": 2,
                    "jeh": 4,
                    "price_ht": 0
                }
            ]
        }
    })

    assert results["RULE_010"]["status"] == "COMPLIANT"


def test_phase_identity_mismatch():
    results = run({
        "methodology": {
            "phases": [
                {"number": 1, "title": "Cadrage"}
            ]
        },
        "planning": {
            "phases": [
                {"number": 1, "title": "Cadrage"}
            ]
        },
        "budget": {
            "phases": [
                {"number": 1, "title": "Cadrage projet"}
            ]
        }
    })

    assert results["RULE_015"]["status"] == "NON_COMPLIANT"


def test_total_duration_with_parallel_phases():
    results = run({
        "planning": {
            "total_duration_weeks": 5,
            "phases": [
                {
                    "number": 1,
                    "start_week": 1,
                    "end_week": 3
                },
                {
                    "number": 2,
                    "start_week": 2,
                    "end_week": 5
                }
            ]
        }
    })

    assert results["RULE_017"]["status"] == "COMPLIANT"

def test_unit_jeh_price():
    results = run({
        "budget": {
            "phases": [
                {
                    "number": 1,
                    "title": "Développement",
                    "jeh": 4,
                    "price_ht": 1200
                }
            ]
        }
    })

    assert results["RULE_023"]["status"] == "COMPLIANT"