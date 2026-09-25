import json
from pathlib import Path

from src.rules.llm import run_llm_rules


DOCUMENT_PATH = Path(
    "data/normalized/real_proposal.json"
)


def load_document() -> dict:
    return json.loads(
        DOCUMENT_PATH.read_text(
            encoding="utf-8"
        )
    )


def main():
    document = load_document()

    print("=" * 80)
    print("LLM ENGINE V2 — real_proposal.json")
    print("=" * 80)

    results = run_llm_rules(
        normalized_document=document
    )

    print(
        f"{len(results)} résultats reçus\n"
    )

    for result in results:
        rule_id = result["rule_id"]
        status = result["status"]
        reason = result.get("reason")
        evidence = result.get("evidence")
        recommendation = result.get(
            "recommendation"
        )

        print(
            f"{rule_id:<10} "
            f"{status:<16} "
            f"| {reason}"
        )

        if evidence:
            print(
                f"{'':<27}↳ Evidence: {evidence}"
            )

        if recommendation:
            print(
                f"{'':<27}↳ Recommendation: "
                f"{recommendation}"
            )

        print()


if __name__ == "__main__":
    main()