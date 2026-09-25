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


def main():
    for filename in FILES:
        inspect_document(filename)


if __name__ == "__main__":
    main()