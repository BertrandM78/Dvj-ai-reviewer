from unittest import result

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


def test_reference_without_proposal_date():
    results = run({
        "metadata": {
            "proposal_reference": "DE-0926-1042-1088-1121",
            "proposal_date": None,
        }
    })

    assert results["RULE_002"]["status"] == "NOT_EVALUATED"

def test_jeh_free_methodology_phase_can_be_absent_from_budget():
    results = run({
        "methodology": {
            "phases": [
                {
                    "number": 1,
                    "title": "Cadrage",
                    "jeh": 5,
                    "price_ht": 2000,
                },
                {
                    "number": 2,
                    "title": "RSE",
                    "jeh": 1,
                    "price_ht": 0,
                },
            ]
        },
        "budget": {
            "phases": [
                {
                    "number": 1,
                    "title": "Cadrage",
                    "jeh": 5,
                    "price_ht": 2000,
                },
            ]
        },
    })

    assert results["RULE_020"]["status"] == "COMPLIANT"


def test_jeh_paid_methodology_phase_cannot_be_absent_from_budget():
    results = run({
        "methodology": {
            "phases": [
                {
                    "number": 1,
                    "title": "Cadrage",
                    "jeh": 5,
                    "price_ht": 2000,
                },
                {
                    "number": 2,
                    "title": "Analyse",
                    "jeh": 4,
                    "price_ht": 1200,
                },
            ]
        },
        "budget": {
            "phases": [
                {
                    "number": 1,
                    "title": "Cadrage",
                    "jeh": 5,
                    "price_ht": 2000,
                },
            ]
        },
    })

    assert results["RULE_020"]["status"] == "NON_COMPLIANT"

def test_price_free_methodology_phase_can_be_absent_from_budget():
    results = run({
        "methodology": {
            "phases": [
                {
                    "number": 1,
                    "title": "Cadrage",
                    "price_ht": 2000,
                },
                {
                    "number": 2,
                    "title": "RSE",
                    "price_ht": 0,
                },
            ]
        },
        "budget": {
            "phases": [
                {
                    "number": 1,
                    "title": "Cadrage",
                    "price_ht": 2000,
                },
            ]
        },
    })

    assert results["RULE_021"]["status"] == "COMPLIANT"


def test_price_paid_methodology_phase_cannot_be_absent_from_budget():
    results = run({
        "methodology": {
            "phases": [
                {
                    "number": 1,
                    "title": "Cadrage",
                    "price_ht": 2000,
                },
                {
                    "number": 2,
                    "title": "Analyse",
                    "price_ht": 1200,
                },
            ]
        },
        "budget": {
            "phases": [
                {
                    "number": 1,
                    "title": "Cadrage",
                    "price_ht": 2000,
                },
            ]
        },
    })

    assert results["RULE_021"]["status"] == "NON_COMPLIANT"


def test_phase_identity_allows_free_phase_missing_from_budget():
    results = run({
        "methodology": {
            "phases": [
                {
                    "number": 1,
                    "title": "Cadrage",
                    "price_ht": 2000,
                },
                {
                    "number": 2,
                    "title": "RSE",
                    "price_ht": 0,
                },
            ]
        },
        "planning": {
            "phases": [
                {
                    "number": 1,
                    "title": "Cadrage",
                },
                {
                    "number": 2,
                    "title": "RSE",
                },
            ]
        },
        "budget": {
            "phases": [
                {
                    "number": 1,
                    "title": "Cadrage",
                    "price_ht": 2000,
                },
            ]
        },
    })

    assert results["RULE_015"]["status"] == "COMPLIANT"


def test_phase_identity_rejects_paid_phase_missing_from_budget():
    results = run({
        "methodology": {
            "phases": [
                {
                    "number": 1,
                    "title": "Cadrage",
                    "price_ht": 2000,
                },
                {
                    "number": 2,
                    "title": "Analyse",
                    "price_ht": 1200,
                },
            ]
        },
        "planning": {
            "phases": [
                {
                    "number": 1,
                    "title": "Cadrage",
                },
                {
                    "number": 2,
                    "title": "Analyse",
                },
            ]
        },
        "budget": {
            "phases": [
                {
                    "number": 1,
                    "title": "Cadrage",
                    "price_ht": 2000,
                },
            ]
        },
    })

    assert results["RULE_015"]["status"] == "NON_COMPLIANT"

def test_client_iterations_above_threshold_is_suggested():
    results = run({
        "methodology": {
            "phases": [
                {
                    "number": 1,
                    "title": "Analyse des besoins clients",
                    "duration_weeks": 2,
                    "client_iterations": 6,
                },
            ]
        },
    })

    assert results["REC_003"]["status"] == "SUGGESTED"


def test_client_iterations_below_threshold_is_not_suggested():
    results = run({
        "methodology": {
            "phases": [
                {
                    "number": 1,
                    "title": "Analyse des besoins clients",
                    "duration_weeks": 2,
                    "client_iterations": 1,
                },
            ]
        },
    })

    assert results["REC_003"]["status"] == "NOT_SUGGESTED"


def test_client_iterations_missing_is_not_evaluated():
    results = run({
        "methodology": {
            "phases": [
                {
                    "number": 1,
                    "title": "Analyse des besoins clients",
                    "duration_weeks": 2,
                    "client_iterations": None,
                },
            ]
        },
    })

    assert results["REC_003"]["status"] == "NOT_EVALUATED"


def test_client_iterations_with_missing_duration_is_not_evaluated():
    results = run({
        "methodology": {
            "phases": [
                {
                    "number": 1,
                    "title": "Analyse des besoins clients",
                    "duration_weeks": None,
                    "client_iterations": 4,
                },
            ]
        },
    })

    assert results["REC_003"]["status"] == "NOT_EVALUATED"


def test_external_costs_absent_without_resources_is_not_applicable():
    results = run({
        "methodology": {
            "phases": [
                {
                    "number": 1,
                    "title": "Analyse",
                    "external_resources": [],
                },
            ]
        },
        "budget": {
            "external_costs": [],
        },
    })

    assert results["RULE_025"]["status"] == "NOT_APPLICABLE"


def test_external_cost_without_resource_is_non_compliant():
    results = run({
        "methodology": {
            "phases": [
                {
                    "number": 1,
                    "title": "Analyse",
                    "external_resources": [],
                },
            ]
        },
        "budget": {
            "external_costs": [
                {
                    "name": "Licence externe",
                    "amount_ht": 500,
                },
            ],
        },
    })

    assert results["RULE_025"]["status"] == "NON_COMPLIANT"


def test_external_resource_without_cost_is_not_evaluated():
    results = run({
        "methodology": {
            "phases": [
                {
                    "number": 1,
                    "title": "Développement",
                    "external_resources": [
                        "OpenAI API",
                    ],
                },
            ]
        },
        "budget": {
            "external_costs": [],
        },
    })

    assert results["RULE_025"]["status"] == "NOT_EVALUATED"


def test_external_resource_with_cost_is_not_evaluated():
    results = run({
        "methodology": {
            "phases": [
                {
                    "number": 1,
                    "title": "Développement",
                    "external_resources": [
                        "OpenAI API",
                    ],
                },
            ]
        },
        "budget": {
            "external_costs": [
                {
                    "name": "API externe",
                    "amount_ht": 300,
                },
            ],
        },
    })

    assert results["RULE_025"]["status"] == "NOT_EVALUATED"

def test_rule_001_compliant_when_all_structure_present():
    rule = next(
        rule
        for rule in load_rules()
        if rule["id"] == "RULE_001"
    )

    document = {
        "slides": [
            {
                "title": "Étude client",
                "detected_section": "COVER",
            },
            {
                "title": "Présentation DVJ",
                "detected_section": "ABOUT_DVJ",
            },
            {
                "title": "Notre compréhension de votre besoin",
                "detected_section": "CLIENT_NEED",
            },
            {
                "title": "Nos références",
                "detected_section": "REFERENCES",
            },
            {
                "title": "Notre méthodologie",
                "detected_section": "METHODOLOGY",
            },
            {
                "title": "Planning",
                "detected_section": "PLANNING",
            },
            {
                "title": "Budget",
                "detected_section": "BUDGET",
            },
            {
                "title": "L'équipe",
                "detected_section": "TEAM",
            },
            {
                "title": "Notre démarche responsable",
                "detected_section": "RSE",
            },
            {
                "title": "On poursuit ensemble",
                "detected_section": "OTHER",
            },
            {
                "title": "Boostez votre entreprise",
                "detected_section": "OTHER",
            },
            {
                "title": "Nos coordonnées",
                "detected_section": "CONTACT",
            },
        ],
        "solution": {
            "summary": "Solution proposée au client."
        },
    }

    results = run_deterministic_rules(
        document,
        rules=[rule],
    )

    assert results[0]["status"] == "COMPLIANT"


def test_rule_001_detects_missing_required_items():
    rule = next(
        rule
        for rule in load_rules()
        if rule["id"] == "RULE_001"
    )

    document = {
        "slides": [
            {
                "title": "Étude client",
                "detected_section": "COVER",
            },
            {
                "title": "Méthodologie",
                "detected_section": "METHODOLOGY",
            },
            {
                "title": "Budget",
                "detected_section": "BUDGET",
            },
        ],
        "solution": {
            "summary": "Solution."
        },
    }

    results = run_deterministic_rules(
        document,
        rules=[rule],
    )

    result = results[0]

    assert "Planning" in result["evidence"]
    assert "Présentation de l'équipe" in result["evidence"]

    assert "Page de couverture" not in result["evidence"].split(
        "Éléments manquants :"
    )[1].split("Éléments détectés :")[0]

    assert "Méthodologie" not in result["evidence"].split(
        "Éléments manquants :"
    )[1].split("Éléments détectés :")[0]

    assert "Budget" not in result["evidence"].split(
        "Éléments manquants :"
    )[1].split("Éléments détectés :")[0]

def test_rule_001_accepts_all_required_structural_sections():
    rule = next(
        rule
        for rule in load_rules()
        if rule["id"] == "RULE_001"
    )

    document = {
        "slides": [
            {
                "title": "Étude client",
                "detected_section": "COVER",
            },
            {
                "title": "Nos expériences",
                "detected_section": "REFERENCES",
            },
            {
                "title": "Notre méthodologie",
                "detected_section": "METHODOLOGY",
            },
            {
                "title": "Calendrier",
                "detected_section": "PLANNING",
            },
            {
                "title": "Proposition financière",
                "detected_section": "BUDGET",
            },
            {
                "title": "Équipe projet",
                "detected_section": "TEAM",
            },
        ],
        "solution": {
            "summary": "Solution proposée au client."
        },
    }

    results = run_deterministic_rules(
        document,
        rules=[rule],
    )

    result = results[0]

    assert result["status"] == "COMPLIANT"