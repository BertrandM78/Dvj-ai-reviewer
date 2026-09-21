from pathlib import Path

from src.deterministic_rules import check_rule_23
from src.document_parser import extract_pdf_text
from src.document_normalizer import normalize_document


def test_case(name: str, text: str, expected: str) -> None:
    normalized = normalize_document(text)

    result = check_rule_23(normalized)

    actual = result["status"]
    symbol = "✓" if actual == expected else "✗"

    print()
    print("=" * 70)
    print(f"{symbol} {name}")
    print(f"Expected:  {expected}")
    print(f"Actual:    {actual}")
    print(f"Evidence:  {result.get('evidence')}")
    print(f"Reasoning: {result.get('reasoning')}")

    assert actual == expected, (
        f"{name}: expected {expected}, got {actual}"
    )


p001 = Path(
    "data/test_proposals/proposal_001.txt"
).read_text(encoding="utf-8")

p002 = Path(
    "data/test_proposals/proposal_002.txt"
).read_text(encoding="utf-8")

pdf_text = extract_pdf_text(
    Path(
        "data/test_proposals/DE-0426-1002-1017-1075.pdf"
    )
)


test_case(
    "P001 synthetic",
    p001,
    "COMPLIANT",
)

test_case(
    "P002 synthetic",
    p002,
    "NON_COMPLIANT",
)

test_case(
    "Real PDF",
    pdf_text,
    "COMPLIANT",
)

print()
print("✓ All RULE_23 tests passed.")