import json
from pathlib import Path

from src.rules.loader import load_rules
from src.rules.deterministic import run_deterministic_rules


DATA_DIR = Path("data/normalized")

FILES = [
    "P001.json",
    "P002.json",
    "real_proposal.json",
]


def load_document(filename: str) -> dict:
    path = DATA_DIR / filename

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def inspect_document(filename: str) -> None:
    document = load_document(filename)

    results = run_deterministic_rules(
        normalized_document=document,
        rules=load_rules(),
    )

    print()
    print("=" * 80)
    print(filename)
    print("=" * 80)

    for result in results:
        print(
            f"{result['rule_id']:<10} "
            f"{result['status']:<16} "
            f"| {result['reason']}"
        )

        if result.get("evidence"):
            print(
                f"{'':<27}"
                f"↳ {result['evidence']}"
            )

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

    assert result["status"] == "NON_COMPLIANT"
    assert "Qui sommes-nous" in result["evidence"]
    assert "RSE" in result["evidence"]

def test_rule_001_exact_or_close_does_not_accept_semantic_section_only():
    rule = next(
        rule
        for rule in load_rules()
        if rule["id"] == "RULE_001"
    )

    document = {
        "slides": [
            {
                "title": "Présentation des besoins du projet",
                "detected_section": "CLIENT_NEED",
            },
        ],
        "solution": {},
    }

    results = run_deterministic_rules(
        document,
        rules=[rule],
    )

    result = results[0]

    assert result["status"] == "NON_COMPLIANT"

    assert (
        "Notre compréhension de votre besoin"
        in result["evidence"]
    )

def main():
    for filename in FILES:
        inspect_document(filename)


if __name__ == "__main__":
    main()