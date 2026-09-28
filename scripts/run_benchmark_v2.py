"""
Run the frozen V2 reviewer benchmark on the 5 evaluation proposals.

Pipeline:
    PDF
    -> extract_pdf_text()
    -> normalize_document()
    -> review_v2()
    -> data/evaluation/predictions/P00X.json

Important:
- This script DOES NOT evaluate performance.
- It DOES NOT modify ground truth.
- It DOES NOT modify reviewer rules or prompts.
- Predictions are saved raw enough to be evaluated later.
"""

import argparse
import json
from pathlib import Path
from typing import Any

from src.document_parser import extract_pdf_text
from src.document_normalizer import normalize_document
from src.reviewer_v2 import review_v2


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT_DIR = Path(__file__).resolve().parents[1]

PROPOSALS_DIR = ROOT_DIR / "data" / "test_proposals"
GROUND_TRUTH_DIR = ROOT_DIR / "data" / "evaluation" / "ground_truth"
PREDICTIONS_DIR = ROOT_DIR / "data" / "evaluation" / "predictions"
NORMALIZED_DIR = ROOT_DIR / "data" / "normalized"


# ---------------------------------------------------------------------------
# Frozen benchmark mapping
# ---------------------------------------------------------------------------

PROPOSALS = {
    "P001": "DE-0926-1044-1068-1102.pdf",
    "P002": "DE-0926-1045-1069-1103.pdf",
    "P003": "DE-0926-1046-1070-1104.pdf",
    "P004": "DE-0926-1047-1071-1105.pdf",
    "P005": "DE-0926-1048-1072-1106.pdf",
}

EXPECTED_RULE_COUNT = 28

VALID_GT_STATUSES = {
    "COMPLIANT",
    "NON_COMPLIANT",
    "NOT_EVALUATED",
    "NOT_APPLICABLE",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_json(path: Path) -> dict:
    """Load a JSON file."""
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data: Any, path: Path) -> None:
    """Save JSON with readable UTF-8 formatting."""
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2,
            default=str,
        )


def validate_benchmark() -> None:
    """
    Validate the benchmark BEFORE any Bedrock call.

    Checks:
    - all PDFs exist
    - all ground-truth files exist
    - P00X -> PDF -> proposal_id mapping is correct
    - each ground truth contains exactly 28 rules
    - rule IDs RULE_001 ... RULE_028 are present
    - ground-truth statuses are valid
    """

    print("\n=== VALIDATING BENCHMARK ===\n")

    expected_rule_ids = {
        f"RULE_{i:03d}"
        for i in range(1, EXPECTED_RULE_COUNT + 1)
    }

    errors = []

    for benchmark_id, pdf_name in PROPOSALS.items():

        pdf_path = PROPOSALS_DIR / pdf_name
        gt_path = GROUND_TRUTH_DIR / f"{benchmark_id}.json"

        # ---------------------------------------------------------------
        # File existence
        # ---------------------------------------------------------------

        if not pdf_path.exists():
            errors.append(
                f"{benchmark_id}: PDF missing -> {pdf_path}"
            )
            continue

        if not gt_path.exists():
            errors.append(
                f"{benchmark_id}: ground truth missing -> {gt_path}"
            )
            continue

        # ---------------------------------------------------------------
        # Load ground truth
        # ---------------------------------------------------------------

        try:
            ground_truth = load_json(gt_path)
        except Exception as exc:
            errors.append(
                f"{benchmark_id}: cannot read ground truth -> {exc}"
            )
            continue

        # ---------------------------------------------------------------
        # Verify mapping
        # ---------------------------------------------------------------

        expected_reference = pdf_path.stem
        actual_reference = ground_truth.get("proposal_id")

        if actual_reference != expected_reference:
            errors.append(
                f"{benchmark_id}: mapping mismatch "
                f"(PDF={expected_reference}, GT={actual_reference})"
            )

        # ---------------------------------------------------------------
        # Verify rules
        # ---------------------------------------------------------------

        rules = ground_truth.get("rules")

        if not isinstance(rules, dict):
            errors.append(
                f"{benchmark_id}: missing or invalid 'rules' object"
            )
            continue

        actual_rule_ids = set(rules.keys())

        missing_rules = expected_rule_ids - actual_rule_ids
        unexpected_rules = actual_rule_ids - expected_rule_ids

        if missing_rules:
            errors.append(
                f"{benchmark_id}: missing rules -> "
                f"{sorted(missing_rules)}"
            )

        if unexpected_rules:
            errors.append(
                f"{benchmark_id}: unexpected rules -> "
                f"{sorted(unexpected_rules)}"
            )

        if len(rules) != EXPECTED_RULE_COUNT:
            errors.append(
                f"{benchmark_id}: expected "
                f"{EXPECTED_RULE_COUNT} rules, found {len(rules)}"
            )

        # ---------------------------------------------------------------
        # Verify statuses
        # ---------------------------------------------------------------

        for rule_id, rule_data in rules.items():

            if not isinstance(rule_data, dict):
                errors.append(
                    f"{benchmark_id} / {rule_id}: "
                    "rule must be an object"
                )
                continue

            status = rule_data.get("status")

            if status not in VALID_GT_STATUSES:
                errors.append(
                    f"{benchmark_id} / {rule_id}: "
                    f"invalid status '{status}'"
                )

        if not errors or not any(
            error.startswith(f"{benchmark_id}:")
            or error.startswith(f"{benchmark_id} /")
            for error in errors
        ):
            print(
                f"✓ {benchmark_id}: "
                f"{expected_reference} "
                f"({len(rules)} rules)"
            )

    # -------------------------------------------------------------------
    # Stop before AWS if anything is wrong
    # -------------------------------------------------------------------

    if errors:
        print("\nBenchmark validation FAILED:\n")

        for error in errors:
            print(f"  ✗ {error}")

        raise SystemExit(
            "\nFix the benchmark before running Bedrock."
        )

    print("\n✓ Benchmark mapping and ground truths are valid.")
    print(
        f"✓ {len(PROPOSALS)} proposals × "
        f"{EXPECTED_RULE_COUNT} rules = "
        f"{len(PROPOSALS) * EXPECTED_RULE_COUNT} ground-truth decisions."
    )


def normalize_prediction_results(results: Any) -> list:
    """
    Convert review_v2 output into a JSON-serializable list.

    Expected reviewer output is normally a list of dictionaries.
    This helper also tolerates simple object-like results.
    """

    if results is None:
        return []

    if isinstance(results, dict):
        # In case review_v2 returns {"results": [...]}
        if "results" in results and isinstance(results["results"], list):
            results = results["results"]
        else:
            return [results]

    if not isinstance(results, list):
        raise TypeError(
            "review_v2() must return a list or a dict containing 'results'. "
            f"Received: {type(results).__name__}"
        )

    normalized_results = []

    for result in results:

        if isinstance(result, dict):
            normalized_results.append(result)

        elif hasattr(result, "__dict__"):
            normalized_results.append(vars(result))

        else:
            raise TypeError(
                "Unsupported reviewer result type: "
                f"{type(result).__name__}"
            )

    return normalized_results


def validate_prediction(
    benchmark_id: str,
    results: list,
) -> None:
    """
    Perform basic integrity checks on reviewer output.

    The V2 reviewer currently returns 35 results:
    28 obligations + recommendations,
    with RAW_TEXT_LLM excluded where applicable.

    For the benchmark itself, evaluate.py will later select RULE_001..RULE_028.
    """

    if not results:
        raise ValueError(
            f"{benchmark_id}: reviewer returned no results"
        )

    rule_ids = []

    for result in results:
        rule_id = result.get("rule_id")

        if rule_id:
            rule_ids.append(rule_id)

    duplicates = {
        rule_id
        for rule_id in rule_ids
        if rule_ids.count(rule_id) > 1
    }

    if duplicates:
        raise ValueError(
            f"{benchmark_id}: duplicate rule IDs in prediction: "
            f"{sorted(duplicates)}"
        )

    required_rules = {
        f"RULE_{i:03d}"
        for i in range(1, EXPECTED_RULE_COUNT + 1)
    }

    predicted_rule_ids = set(rule_ids)

    missing = required_rules - predicted_rule_ids

    if missing:
        raise ValueError(
            f"{benchmark_id}: reviewer did not return "
            f"required rules: {sorted(missing)}"
        )


# ---------------------------------------------------------------------------
# Run one proposal
# ---------------------------------------------------------------------------

def run_proposal(
    benchmark_id: str,
    pdf_name: str,
    force: bool = False,
) -> None:

    pdf_path = PROPOSALS_DIR / pdf_name
    prediction_path = (
        PREDICTIONS_DIR / f"{benchmark_id}.json"
    )

    print("\n" + "=" * 70)
    print(f"{benchmark_id} — {pdf_path.stem}")
    print("=" * 70)

    # -------------------------------------------------------------------
    # Protect frozen predictions
    # -------------------------------------------------------------------

    if prediction_path.exists() and not force:
        print(
            f"SKIPPED: prediction already exists -> "
            f"{prediction_path}"
        )
        print(
            "Use --force only if you intentionally want "
            "to regenerate predictions."
        )
        return

    # -------------------------------------------------------------------
    # 1. Extract PDF
    # -------------------------------------------------------------------

    print("[1/3] Extracting PDF...")

    raw_text = extract_pdf_text(str(pdf_path))

    if not raw_text or not raw_text.strip():
        raise ValueError(
            f"{benchmark_id}: PDF extraction returned empty text"
        )

    print(
        f"      ✓ {len(raw_text):,} characters extracted"
    )

    # -------------------------------------------------------------------
    # 2. Normalize document
    # -------------------------------------------------------------------

    print("[2/3] Normalizing document with Bedrock...")

    normalized_document = normalize_document(raw_text)

    if not normalized_document:
        raise ValueError(
            f"{benchmark_id}: normalizer returned empty output"
        )
    NORMALIZED_DIR.mkdir(parents=True, exist_ok=True)

    normalized_path = NORMALIZED_DIR / f"{benchmark_id}.json"

    with normalized_path.open("w", encoding="utf-8") as f:
        json.dump(
            normalized_document,
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(f"      ✓ normalized document saved -> {normalized_path}")

    print("      ✓ document normalized")

    # -------------------------------------------------------------------
    # 3. Run V2 reviewer
    # -------------------------------------------------------------------

    print("[3/3] Running V2 reviewer...")

    reviewer_output = review_v2(normalized_document)

    results = normalize_prediction_results(
        reviewer_output
    )

    validate_prediction(
        benchmark_id=benchmark_id,
        results=results,
    )

    print(
        f"      ✓ reviewer returned "
        f"{len(results)} results"
    )

    # -------------------------------------------------------------------
    # Save prediction
    # -------------------------------------------------------------------

    prediction = {
        "benchmark_id": benchmark_id,
        "proposal_id": pdf_path.stem,
        "benchmark_version": "v2",
        "prediction_source": "reviewer_v2",
        "results": results,
    }

    save_json(
        prediction,
        prediction_path,
    )

    print(
        f"      ✓ saved -> "
        f"{prediction_path.relative_to(ROOT_DIR)}"
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:

    parser = argparse.ArgumentParser(
        description=(
            "Run the frozen DVJ Proposal Reviewer V2 benchmark."
        )
    )

    parser.add_argument(
        "--validate-only",
        action="store_true",
        help=(
            "Validate PDF/ground-truth mappings without "
            "calling Bedrock."
        ),
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help=(
            "Overwrite existing prediction files. "
            "Avoid using this during the official benchmark."
        ),
    )

    parser.add_argument(
        "--proposal",
        choices=list(PROPOSALS.keys()),
        help=(
            "Run only one proposal, e.g. --proposal P001. "
            "Default: run all five."
        ),
    )

    args = parser.parse_args()

    # -------------------------------------------------------------------
    # Always validate before AWS calls
    # -------------------------------------------------------------------

    validate_benchmark()

    if args.validate_only:
        print(
            "\nValidation only: no Bedrock calls were made."
        )
        return

    # -------------------------------------------------------------------
    # Prepare predictions directory
    # -------------------------------------------------------------------

    PREDICTIONS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # -------------------------------------------------------------------
    # Select proposals
    # -------------------------------------------------------------------

    if args.proposal:
        proposals_to_run = {
            args.proposal: PROPOSALS[args.proposal]
        }
    else:
        proposals_to_run = PROPOSALS

    # -------------------------------------------------------------------
    # Run benchmark
    # -------------------------------------------------------------------

    print("\n=== RUNNING V2 BENCHMARK ===")

    completed = 0
    failed = []

    for benchmark_id, pdf_name in proposals_to_run.items():

        try:
            run_proposal(
                benchmark_id=benchmark_id,
                pdf_name=pdf_name,
                force=args.force,
            )

            completed += 1

        except Exception as exc:
            failed.append(
                (benchmark_id, str(exc))
            )

            print(
                f"\n✗ {benchmark_id} FAILED: {exc}"
            )

    # -------------------------------------------------------------------
    # Summary
    # -------------------------------------------------------------------

    print("\n" + "=" * 70)
    print("BENCHMARK RUN COMPLETE")
    print("=" * 70)

    print(
        f"Successful / skipped safely: "
        f"{completed}/{len(proposals_to_run)}"
    )

    if failed:
        print("\nFailures:")

        for benchmark_id, error in failed:
            print(
                f"  ✗ {benchmark_id}: {error}"
            )

        raise SystemExit(1)

    print(
        "\nPredictions available in:"
    )
    print(
        f"  {PREDICTIONS_DIR.relative_to(ROOT_DIR)}/"
    )

    print(
        "\nDo NOT modify the reviewer before evaluating "
        "these predictions."
    )


if __name__ == "__main__":
    main()