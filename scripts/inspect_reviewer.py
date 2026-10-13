import json
from pathlib import Path
from collections import Counter

from src.reviewer import review
from src.rules.loader import load_rules


DOCUMENT_PATH = Path(
    "data/normalized/real_proposal.json"
)


def main():
    normalized_document = json.loads(
        DOCUMENT_PATH.read_text(
            encoding="utf-8"
        )
    )

    rules = load_rules()

    rules_by_id = {
        rule["id"]: rule
        for rule in rules
    }

    print("=" * 70)
    print("# REVIEWER V2 — REAL PROPOSAL")
    print("=" * 70)

    results = review(
        normalized_document
    )

    print()
    print(f"{len(results)} résultats reçus")

    engine_counts = Counter(
        rules_by_id[result["rule_id"]]["engine"]
        for result in results
    )

    status_counts = Counter(
        result["status"]
        for result in results
    )

    print(f"Engines : {dict(engine_counts)}")
    print(f"Statuses: {dict(status_counts)}")

    print()
    print("-" * 70)

    for result in results:
        rule_id = result["rule_id"]
        engine = rules_by_id[rule_id]["engine"]

        print(
            f"\n{rule_id:<10} "
            f"{result['status']:<16} "
            f"[{engine}]"
        )

        print(
            f"↳ {result.get('reason')}"
        )

        if result.get("evidence"):
            print(
                f"↳ Evidence: "
                f"{result['evidence']}"
            )

        if result.get("recommendation"):
            print(
                f"↳ Recommendation: "
                f"{result['recommendation']}"
            )

    print()
    print("=" * 70)
    print("# INTEGRITY CHECKS")
    print("=" * 70)

    result_ids = {
        result["rule_id"]
        for result in results
    }

    assert "RULE_001" in result_ids
    assert (
        rules_by_id["RULE_001"]["engine"]
        == "DETERMINISTIC"
    )

    assert len(results) == 35
    assert engine_counts["DETERMINISTIC"] == 16
    assert engine_counts["LLM"] == 19

    assert "REC_003" in result_ids
    assert (
        rules_by_id["REC_003"]["engine"]
        == "DETERMINISTIC"
    )

    assert "RULE_025" in result_ids
    assert (
        rules_by_id["RULE_025"]["engine"]
        == "DETERMINISTIC"
    )

    assert "REC_005" not in result_ids
    assert (
        rules_by_id["REC_005"]["engine"]
        == "RAW_TEXT_LLM"
    )


    print("✓ 35 résultats")
    print("✓ 16 DETERMINISTIC")
    print("✓ 19 LLM")
    print("✓ RULE_001 évaluée par DETERMINISTIC")
    print("✓ REC_003 évaluée par DETERMINISTIC")
    print("✓ RULE_025 évaluée par DETERMINISTIC")
    print("✓ REC_005 exclue du pipeline actuel")
    print()
    print("REVIEWER V2 INTEGRITY: OK")


if __name__ == "__main__":
    main()