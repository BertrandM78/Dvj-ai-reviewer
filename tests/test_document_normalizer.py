import json
from pathlib import Path

from src.document_normalizer import normalize_document
from src.document_parser import extract_pdf_text

TEST_DIR = Path("data/test_proposals")


def run_normalization(name: str, text: str) -> None:
    print()
    print("=" * 70)
    print(name)
    print("=" * 70)

    normalized = normalize_document(text)

    print(
        json.dumps(
            normalized,
            indent=2,
            ensure_ascii=False,
        )
    )


p001 = (TEST_DIR / "proposal_001.txt").read_text(
    encoding="utf-8"
)

p002 = (TEST_DIR / "proposal_002.txt").read_text(
    encoding="utf-8"
)

pdf = extract_pdf_text(
    TEST_DIR / "DE-0426-1002-1017-1075.pdf"
)


run_normalization(
    "P001 SYNTHETIC",
    p001,
)

run_normalization(
    "P002 SYNTHETIC",
    p002,
)

run_normalization(
    "REAL PDF",
    pdf,
)