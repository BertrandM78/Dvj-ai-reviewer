import json
from pathlib import Path

from src.document_normalizer import normalize_document
from src.document_parser import extract_pdf_text


TEST_DIR = Path("data/test_proposals")
OUTPUT_DIR = Path("data/normalized")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def run_normalization(
    name: str,
    text: str,
    output_filename: str,
) -> None:
    print()
    print("=" * 70)
    print(name)
    print("=" * 70)

    normalized = normalize_document(text)

    output_path = OUTPUT_DIR / output_filename

    output_path.write_text(
        json.dumps(
            normalized,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print(
        json.dumps(
            normalized,
            indent=2,
            ensure_ascii=False,
        )
    )

    print(f"\nSaved to: {output_path}")


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
    "P001.json",
)

run_normalization(
    "P002 SYNTHETIC",
    p002,
    "P002.json",
)

run_normalization(
    "REAL PDF",
    pdf,
    "real_proposal.json",
)