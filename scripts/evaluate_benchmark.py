"""
Evaluate the frozen DVJ Proposal Reviewer V2 benchmark.

Inputs:
    data/evaluation/ground_truth/P001.json ... P005.json
    data/evaluation/predictions/P001.json ... P005.json

Outputs:
    data/evaluation/benchmark.json
    data/evaluation/benchmark.md

No AWS / Bedrock calls are made.

Evaluation scope:
    RULE_001 ... RULE_028 only.
    Recommendations are excluded.

Main metrics:
    - 4-class accuracy
    - 4x4 confusion matrix
    - violation precision
    - violation recall
    - violation F1
    - abstention rate
    - NOT_APPLICABLE accuracy
    - per-proposal metrics
    - detailed error list
"""

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Paths / benchmark definition
# ---------------------------------------------------------------------------

ROOT_DIR = Path(__file__).resolve().parents[1]

EVALUATION_DIR = ROOT_DIR / "data" / "evaluation"
GROUND_TRUTH_DIR = EVALUATION_DIR / "ground_truth"
PREDICTIONS_DIR = EVALUATION_DIR / "predictions"

DEFAULT_JSON_REPORT = EVALUATION_DIR / "benchmark.json"
DEFAULT_MD_REPORT = EVALUATION_DIR / "benchmark.md"

PROPOSAL_IDS = [
    "P001",
    "P002",
    "P003",
    "P004",
    "P005",
]

RULE_IDS = [
    f"RULE_{i:03d}"
    for i in range(1, 29)
]

STATUSES = [
    "COMPLIANT",
    "NON_COMPLIANT",
    "NOT_EVALUATED",
    "NOT_APPLICABLE",
]

VALID_STATUSES = set(STATUSES)


# ---------------------------------------------------------------------------
# JSON helpers
# ---------------------------------------------------------------------------

def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2,
            default=str,
        )


# ---------------------------------------------------------------------------
# Prediction parsing
# ---------------------------------------------------------------------------

def extract_prediction_results(prediction: dict) -> list[dict]:
    """
    Extract the reviewer results list from a saved prediction.

    Expected format from run_benchmark.py:

    {
        "benchmark_id": "P001",
        "proposal_id": "...",
        "benchmark_version": "v2",
        "prediction_source": "reviewer",
        "results": [...]
    }
    """

    results = prediction.get("results")

    if not isinstance(results, list):
        raise ValueError(
            "Prediction must contain a 'results' list."
        )

    return results


def build_prediction_map(
    prediction: dict,
    proposal_id: str,
) -> dict[str, dict]:
    """
    Convert prediction results into:

        {
            "RULE_001": {...},
            ...
        }

    Recommendations and other non-benchmark results are ignored.
    """

    results = extract_prediction_results(prediction)

    prediction_map = {}

    for result in results:

        if not isinstance(result, dict):
            raise ValueError(
                f"{proposal_id}: prediction result is not an object"
            )

        rule_id = result.get("rule_id")

        if rule_id not in RULE_IDS:
            # Recommendations etc. are intentionally excluded.
            continue

        if rule_id in prediction_map:
            raise ValueError(
                f"{proposal_id}: duplicate prediction for {rule_id}"
            )

        prediction_map[rule_id] = result

    return prediction_map


def get_prediction_status(
    result: dict,
    proposal_id: str,
    rule_id: str,
) -> str:
    """
    Extract and validate predicted status.

    V2 is expected to expose:
        result["status"]

    A clear error is raised otherwise.
    """

    status = result.get("status")

    if status is None:
        raise ValueError(
            f"{proposal_id} / {rule_id}: "
            "prediction has no 'status' field. "
            f"Available fields: {sorted(result.keys())}"
        )

    if not isinstance(status, str):
        raise ValueError(
            f"{proposal_id} / {rule_id}: "
            f"status must be a string, got {type(status).__name__}"
        )

    status = status.strip().upper()

    if status not in VALID_STATUSES:
        raise ValueError(
            f"{proposal_id} / {rule_id}: "
            f"invalid predicted status '{status}'"
        )

    return status


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------

def validate_and_load() -> dict:
    """
    Validate all 5 GT/prediction pairs before computing metrics.

    Returns:
        {
            "P001": {
                "ground_truth": ...,
                "prediction": ...,
                "prediction_map": ...
            },
            ...
        }
    """

    print("\n=== VALIDATING BENCHMARK FILES ===\n")

    loaded = {}
    errors = []

    for proposal_id in PROPOSAL_IDS:

        gt_path = GROUND_TRUTH_DIR / f"{proposal_id}.json"
        pred_path = PREDICTIONS_DIR / f"{proposal_id}.json"

        if not gt_path.exists():
            errors.append(
                f"{proposal_id}: missing ground truth -> {gt_path}"
            )
            continue

        if not pred_path.exists():
            errors.append(
                f"{proposal_id}: missing prediction -> {pred_path}"
            )
            continue

        try:
            ground_truth = load_json(gt_path)
        except Exception as exc:
            errors.append(
                f"{proposal_id}: cannot load ground truth: {exc}"
            )
            continue

        try:
            prediction = load_json(pred_path)
        except Exception as exc:
            errors.append(
                f"{proposal_id}: cannot load prediction: {exc}"
            )
            continue

        # ---------------------------------------------------------------
        # Benchmark ID
        # ---------------------------------------------------------------

        pred_benchmark_id = prediction.get("benchmark_id")

        if (
            pred_benchmark_id is not None
            and pred_benchmark_id != proposal_id
        ):
            errors.append(
                f"{proposal_id}: prediction benchmark_id is "
                f"'{pred_benchmark_id}'"
            )

        # ---------------------------------------------------------------
        # Proposal reference consistency
        # ---------------------------------------------------------------

        gt_reference = ground_truth.get("proposal_id")
        pred_reference = prediction.get("proposal_id")

        if (
            gt_reference
            and pred_reference
            and gt_reference != pred_reference
        ):
            errors.append(
                f"{proposal_id}: proposal reference mismatch "
                f"(GT={gt_reference}, prediction={pred_reference})"
            )

        # ---------------------------------------------------------------
        # Ground truth rules
        # ---------------------------------------------------------------

        gt_rules = ground_truth.get("rules")

        if not isinstance(gt_rules, dict):
            errors.append(
                f"{proposal_id}: GT has no valid 'rules' object"
            )
            continue

        missing_gt_rules = set(RULE_IDS) - set(gt_rules.keys())

        if missing_gt_rules:
            errors.append(
                f"{proposal_id}: GT missing rules "
                f"{sorted(missing_gt_rules)}"
            )

        for rule_id in RULE_IDS:

            if rule_id not in gt_rules:
                continue

            rule_data = gt_rules[rule_id]

            if not isinstance(rule_data, dict):
                errors.append(
                    f"{proposal_id} / {rule_id}: "
                    "GT rule must be an object"
                )
                continue

            status = rule_data.get("status")

            if status not in VALID_STATUSES:
                errors.append(
                    f"{proposal_id} / {rule_id}: "
                    f"invalid GT status '{status}'"
                )

        # ---------------------------------------------------------------
        # Prediction rules
        # ---------------------------------------------------------------

        try:
            prediction_map = build_prediction_map(
                prediction,
                proposal_id,
            )
        except Exception as exc:
            errors.append(str(exc))
            continue

        missing_prediction_rules = (
            set(RULE_IDS) - set(prediction_map.keys())
        )

        if missing_prediction_rules:
            errors.append(
                f"{proposal_id}: prediction missing rules "
                f"{sorted(missing_prediction_rules)}"
            )

        for rule_id, result in prediction_map.items():

            try:
                get_prediction_status(
                    result,
                    proposal_id,
                    rule_id,
                )
            except Exception as exc:
                errors.append(str(exc))

        loaded[proposal_id] = {
            "ground_truth": ground_truth,
            "prediction": prediction,
            "prediction_map": prediction_map,
        }

        if not any(
            error.startswith(proposal_id)
            for error in errors
        ):
            print(
                f"✓ {proposal_id}: "
                f"{len(RULE_IDS)} GT rules + "
                f"{len(prediction_map)} benchmark predictions"
            )

    if errors:
        print("\nValidation FAILED:\n")

        for error in errors:
            print(f"  ✗ {error}")

        raise SystemExit(
            "\nFix benchmark files before evaluating."
        )

    print(
        f"\n✓ {len(PROPOSAL_IDS)} proposals × "
        f"{len(RULE_IDS)} rules = "
        f"{len(PROPOSAL_IDS) * len(RULE_IDS)} decisions."
    )

    return loaded


# ---------------------------------------------------------------------------
# Metrics helpers
# ---------------------------------------------------------------------------

def safe_divide(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0

    return numerator / denominator


def pct(value: float) -> float:
    return round(value * 100, 2)


def empty_confusion_matrix() -> dict:
    return {
        gt_status: {
            pred_status: 0
            for pred_status in STATUSES
        }
        for gt_status in STATUSES
    }


def compute_metrics(decisions: list[dict]) -> dict:
    """
    Compute metrics for a list of decisions.

    Binary violation metrics use only GT COMPLIANT / NON_COMPLIANT.

    Positive class:
        NON_COMPLIANT

    Convention:
        GT NC + Pred NC -> TP
        GT C  + Pred NC -> FP
        GT NC + any non-NC prediction -> FN
        GT C  + Pred C  -> TN

    Predicted NOT_EVALUATED on GT COMPLIANT is an abstention,
    not a false positive.

    GT NOT_EVALUATED and NOT_APPLICABLE are excluded from
    binary violation precision / recall.
    """

    total = len(decisions)

    if total == 0:
        return {}

    correct = sum(
        1
        for d in decisions
        if d["gt_status"] == d["pred_status"]
    )

    # ---------------------------------------------------------------
    # Distributions
    # ---------------------------------------------------------------

    gt_distribution = Counter(
        d["gt_status"]
        for d in decisions
    )

    pred_distribution = Counter(
        d["pred_status"]
        for d in decisions
    )

    # ---------------------------------------------------------------
    # 4x4 confusion matrix
    # ---------------------------------------------------------------

    confusion = empty_confusion_matrix()

    for decision in decisions:
        confusion[
            decision["gt_status"]
        ][
            decision["pred_status"]
        ] += 1

    # ---------------------------------------------------------------
    # Binary violation detection
    # ---------------------------------------------------------------

    binary_decisions = [
        d
        for d in decisions
        if d["gt_status"] in {
            "COMPLIANT",
            "NON_COMPLIANT",
        }
    ]

    tp = sum(
        1
        for d in binary_decisions
        if (
            d["gt_status"] == "NON_COMPLIANT"
            and d["pred_status"] == "NON_COMPLIANT"
        )
    )

    fp = sum(
        1
        for d in binary_decisions
        if (
            d["gt_status"] == "COMPLIANT"
            and d["pred_status"] == "NON_COMPLIANT"
        )
    )

    fn = sum(
        1
        for d in binary_decisions
        if (
            d["gt_status"] == "NON_COMPLIANT"
            and d["pred_status"] != "NON_COMPLIANT"
        )
    )

    tn = sum(
        1
        for d in binary_decisions
        if (
            d["gt_status"] == "COMPLIANT"
            and d["pred_status"] == "COMPLIANT"
        )
    )

    precision = safe_divide(tp, tp + fp)
    recall = safe_divide(tp, tp + fn)

    f1 = safe_divide(
        2 * precision * recall,
        precision + recall,
    )

    # ---------------------------------------------------------------
    # Abstention
    # ---------------------------------------------------------------

    abstentions = sum(
        1
        for d in decisions
        if d["pred_status"] == "NOT_EVALUATED"
    )

    abstention_rate = safe_divide(
        abstentions,
        total,
    )

    # Abstentions specifically on binary C / NC GT.
    binary_abstentions = sum(
        1
        for d in binary_decisions
        if d["pred_status"] == "NOT_EVALUATED"
    )

    binary_abstention_rate = safe_divide(
        binary_abstentions,
        len(binary_decisions),
    )

    # ---------------------------------------------------------------
    # NOT_APPLICABLE accuracy
    # ---------------------------------------------------------------

    na_decisions = [
        d
        for d in decisions
        if d["gt_status"] == "NOT_APPLICABLE"
    ]

    na_correct = sum(
        1
        for d in na_decisions
        if d["pred_status"] == "NOT_APPLICABLE"
    )

    na_accuracy = safe_divide(
        na_correct,
        len(na_decisions),
    )

    # ---------------------------------------------------------------
    # NOT_EVALUATED accuracy
    # ---------------------------------------------------------------

    ne_decisions = [
        d
        for d in decisions
        if d["gt_status"] == "NOT_EVALUATED"
    ]

    ne_correct = sum(
        1
        for d in ne_decisions
        if d["pred_status"] == "NOT_EVALUATED"
    )

    ne_accuracy = safe_divide(
        ne_correct,
        len(ne_decisions),
    )

    return {
        "total_decisions": total,

        "correct_decisions": correct,

        "accuracy": safe_divide(
            correct,
            total,
        ),

        "ground_truth_distribution": {
            status: gt_distribution.get(status, 0)
            for status in STATUSES
        },

        "prediction_distribution": {
            status: pred_distribution.get(status, 0)
            for status in STATUSES
        },

        "confusion_matrix": confusion,

        "binary_violation_detection": {
            "evaluated_decisions": len(binary_decisions),
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "tn": tn,
            "precision": precision,
            "recall": recall,
            "f1": f1,
        },

        "abstention": {
            "count": abstentions,
            "rate": abstention_rate,
            "binary_count": binary_abstentions,
            "binary_rate": binary_abstention_rate,
        },

        "not_applicable": {
            "count": len(na_decisions),
            "correct": na_correct,
            "accuracy": na_accuracy,
        },

        "not_evaluated": {
            "count": len(ne_decisions),
            "correct": ne_correct,
            "accuracy": ne_accuracy,
        },
    }


# ---------------------------------------------------------------------------
# Build decision dataset
# ---------------------------------------------------------------------------

def build_decisions(loaded: dict) -> list[dict]:
    decisions = []

    for proposal_id in PROPOSAL_IDS:

        ground_truth = loaded[proposal_id]["ground_truth"]
        prediction_map = loaded[proposal_id]["prediction_map"]

        gt_rules = ground_truth["rules"]

        for rule_id in RULE_IDS:

            gt_data = gt_rules[rule_id]
            pred_data = prediction_map[rule_id]

            gt_status = gt_data["status"]

            pred_status = get_prediction_status(
                pred_data,
                proposal_id,
                rule_id,
            )

            decision = {
                "proposal_id": proposal_id,
                "proposal_reference": ground_truth.get(
                    "proposal_id"
                ),
                "rule_id": rule_id,
                "gt_status": gt_status,
                "pred_status": pred_status,
                "correct": gt_status == pred_status,
                "gt_reason": gt_data.get("reason"),
                "prediction_explanation": (
                    pred_data.get("explanation")
                    or pred_data.get("reason")
                ),
                "prediction_engine": pred_data.get("engine"),
            }

            decisions.append(decision)

    return decisions


# ---------------------------------------------------------------------------
# Error analysis
# ---------------------------------------------------------------------------

def build_errors(decisions: list[dict]) -> list[dict]:
    errors = []

    for decision in decisions:

        if decision["correct"]:
            continue

        errors.append(
            {
                "proposal_id": decision["proposal_id"],
                "proposal_reference": (
                    decision["proposal_reference"]
                ),
                "rule_id": decision["rule_id"],
                "ground_truth": decision["gt_status"],
                "prediction": decision["pred_status"],
                "ground_truth_reason": (
                    decision["gt_reason"]
                ),
                "prediction_explanation": (
                    decision["prediction_explanation"]
                ),
            }
        )

    return errors


# ---------------------------------------------------------------------------
# Per-proposal metrics
# ---------------------------------------------------------------------------

def compute_per_proposal(
    decisions: list[dict],
) -> dict:

    result = {}

    for proposal_id in PROPOSAL_IDS:

        proposal_decisions = [
            d
            for d in decisions
            if d["proposal_id"] == proposal_id
        ]

        result[proposal_id] = compute_metrics(
            proposal_decisions
        )

    return result


# ---------------------------------------------------------------------------
# Optional engine breakdown
# ---------------------------------------------------------------------------

def compute_engine_breakdown(
    decisions: list[dict],
) -> dict:
    """
    Compute engine-level metrics only if the prediction results
    actually expose an 'engine' field.

    No engine classification is invented.
    """

    engines = sorted(
        {
            d["prediction_engine"]
            for d in decisions
            if d["prediction_engine"]
        }
    )

    result = {}

    for engine in engines:

        engine_decisions = [
            d
            for d in decisions
            if d["prediction_engine"] == engine
        ]

        result[engine] = compute_metrics(
            engine_decisions
        )

    return result


# ---------------------------------------------------------------------------
# Markdown report
# ---------------------------------------------------------------------------

def render_markdown(report: dict) -> str:

    metrics = report["global_metrics"]
    binary = metrics["binary_violation_detection"]
    abstention = metrics["abstention"]

    lines = []

    lines.append("# DVJ Proposal Reviewer — Benchmark V2")
    lines.append("")
    lines.append(
        f"Benchmark: {report['proposal_count']} propositions, "
        f"{report['rules_per_proposal']} obligations par proposition, "
        f"{metrics['total_decisions']} décisions."
    )
    lines.append("")

    # -------------------------------------------------------------------
    # Main metrics
    # -------------------------------------------------------------------

    lines.append("## Résultats globaux")
    lines.append("")

    lines.append(
        f"- Accuracy 4 classes : "
        f"**{pct(metrics['accuracy']):.2f}%** "
        f"({metrics['correct_decisions']}/"
        f"{metrics['total_decisions']})"
    )

    lines.append(
        f"- Violation precision : "
        f"**{pct(binary['precision']):.2f}%**"
    )

    lines.append(
        f"- Violation recall : "
        f"**{pct(binary['recall']):.2f}%**"
    )

    lines.append(
        f"- Violation F1 : "
        f"**{pct(binary['f1']):.2f}%**"
    )

    lines.append(
        f"- Abstention rate : "
        f"**{pct(abstention['rate']):.2f}%** "
        f"({abstention['count']}/"
        f"{metrics['total_decisions']})"
    )

    lines.append(
        f"- NOT_APPLICABLE accuracy : "
        f"**{pct(metrics['not_applicable']['accuracy']):.2f}%** "
        f"({metrics['not_applicable']['correct']}/"
        f"{metrics['not_applicable']['count']})"
    )

    lines.append(
        f"- NOT_EVALUATED accuracy : "
        f"**{pct(metrics['not_evaluated']['accuracy']):.2f}%** "
        f"({metrics['not_evaluated']['correct']}/"
        f"{metrics['not_evaluated']['count']})"
    )

    lines.append("")

    # -------------------------------------------------------------------
    # Binary counts
    # -------------------------------------------------------------------

    lines.append("## Détection des violations")
    lines.append("")

    lines.append(
        "| TP | FP | FN | TN | Décisions C/NC |"
    )
    lines.append(
        "|---:|---:|---:|---:|---:|"
    )
    lines.append(
        f"| {binary['tp']} "
        f"| {binary['fp']} "
        f"| {binary['fn']} "
        f"| {binary['tn']} "
        f"| {binary['evaluated_decisions']} |"
    )
    lines.append("")

    # -------------------------------------------------------------------
    # Distributions
    # -------------------------------------------------------------------

    lines.append("## Distribution des statuts")
    lines.append("")
    lines.append(
        "| Statut | Ground truth | Prédiction |"
    )
    lines.append(
        "|---|---:|---:|"
    )

    for status in STATUSES:
        lines.append(
            f"| {status} "
            f"| {metrics['ground_truth_distribution'][status]} "
            f"| {metrics['prediction_distribution'][status]} |"
        )

    lines.append("")

    # -------------------------------------------------------------------
    # Confusion matrix
    # -------------------------------------------------------------------

    lines.append("## Matrice de confusion")
    lines.append("")
    lines.append(
        "| GT \\ Pred | COMPLIANT | NON_COMPLIANT "
        "| NOT_EVALUATED | NOT_APPLICABLE |"
    )
    lines.append(
        "|---|---:|---:|---:|---:|"
    )

    confusion = metrics["confusion_matrix"]

    for gt_status in STATUSES:

        row = confusion[gt_status]

        lines.append(
            f"| {gt_status} "
            f"| {row['COMPLIANT']} "
            f"| {row['NON_COMPLIANT']} "
            f"| {row['NOT_EVALUATED']} "
            f"| {row['NOT_APPLICABLE']} |"
        )

    lines.append("")

    # -------------------------------------------------------------------
    # Per proposal
    # -------------------------------------------------------------------

    lines.append("## Résultats par proposition")
    lines.append("")

    lines.append(
        "| Proposition | Accuracy | Precision | Recall | F1 | Erreurs |"
    )
    lines.append(
        "|---|---:|---:|---:|---:|---:|"
    )

    for proposal_id, proposal_metrics in (
        report["per_proposal"].items()
    ):

        proposal_binary = (
            proposal_metrics["binary_violation_detection"]
        )

        errors = (
            proposal_metrics["total_decisions"]
            - proposal_metrics["correct_decisions"]
        )

        lines.append(
            f"| {proposal_id} "
            f"| {pct(proposal_metrics['accuracy']):.2f}% "
            f"| {pct(proposal_binary['precision']):.2f}% "
            f"| {pct(proposal_binary['recall']):.2f}% "
            f"| {pct(proposal_binary['f1']):.2f}% "
            f"| {errors} |"
        )

    lines.append("")

    # -------------------------------------------------------------------
    # Engine breakdown if available
    # -------------------------------------------------------------------

    if report["engine_breakdown"]:

        lines.append("## Résultats par moteur")
        lines.append("")

        lines.append(
            "| Engine | Décisions | Accuracy | Precision | Recall | F1 |"
        )
        lines.append(
            "|---|---:|---:|---:|---:|---:|"
        )

        for engine, engine_metrics in (
            report["engine_breakdown"].items()
        ):

            engine_binary = (
                engine_metrics["binary_violation_detection"]
            )

            lines.append(
                f"| {engine} "
                f"| {engine_metrics['total_decisions']} "
                f"| {pct(engine_metrics['accuracy']):.2f}% "
                f"| {pct(engine_binary['precision']):.2f}% "
                f"| {pct(engine_binary['recall']):.2f}% "
                f"| {pct(engine_binary['f1']):.2f}% |"
            )

        lines.append("")

    # -------------------------------------------------------------------
    # Errors
    # -------------------------------------------------------------------

    lines.append("## Erreurs détaillées")
    lines.append("")

    if not report["errors"]:
        lines.append("Aucune erreur.")
        lines.append("")
    else:

        for error in report["errors"]:

            lines.append(
                f"### {error['proposal_id']} — "
                f"{error['rule_id']}"
            )
            lines.append("")

            lines.append(
                f"- Ground truth : "
                f"`{error['ground_truth']}`"
            )

            lines.append(
                f"- Prédiction : "
                f"`{error['prediction']}`"
            )

            if error["ground_truth_reason"]:
                lines.append(
                    f"- Raison GT : "
                    f"{error['ground_truth_reason']}"
                )

            if error["prediction_explanation"]:
                lines.append(
                    f"- Explication modèle : "
                    f"{error['prediction_explanation']}"
                )

            lines.append("")

    # -------------------------------------------------------------------
    # Methodology
    # -------------------------------------------------------------------

    lines.append("## Méthodologie")
    lines.append("")
    lines.append(
        "Les métriques de détection d'anomalies utilisent "
        "uniquement les décisions dont la ground truth est "
        "COMPLIANT ou NON_COMPLIANT. "
        "NON_COMPLIANT est la classe positive."
    )
    lines.append("")
    lines.append(
        "Les ground truths NOT_APPLICABLE et NOT_EVALUATED "
        "sont exclues du calcul de precision/recall/F1 et "
        "évaluées séparément."
    )
    lines.append("")
    lines.append(
        "Une prédiction NOT_EVALUATED sur une règle réellement "
        "NON_COMPLIANT est considérée comme une violation manquée "
        "(false negative). Une prédiction NOT_EVALUATED sur une "
        "règle COMPLIANT est comptabilisée comme abstention et "
        "non comme false positive."
    )
    lines.append("")
    lines.append(
        "Les métriques globales sont calculées en poolant toutes "
        "les décisions. Elles ne correspondent pas à la moyenne "
        "des pourcentages par proposition."
    )
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Console summary
# ---------------------------------------------------------------------------

def print_summary(report: dict) -> None:

    metrics = report["global_metrics"]
    binary = metrics["binary_violation_detection"]

    print("\n" + "=" * 70)
    print("DVJ PROPOSAL REVIEWER — BENCHMARK V2 RESULTS")
    print("=" * 70)

    print(
        f"\nDecisions: "
        f"{metrics['total_decisions']}"
    )

    print(
        f"4-class accuracy: "
        f"{pct(metrics['accuracy']):.2f}% "
        f"({metrics['correct_decisions']}/"
        f"{metrics['total_decisions']})"
    )

    print("\nViolation detection:")

    print(
        f"  Precision: {pct(binary['precision']):.2f}%"
    )

    print(
        f"  Recall:    {pct(binary['recall']):.2f}%"
    )

    print(
        f"  F1:        {pct(binary['f1']):.2f}%"
    )

    print(
        f"  TP={binary['tp']} "
        f"FP={binary['fp']} "
        f"FN={binary['fn']} "
        f"TN={binary['tn']}"
    )

    print(
        f"\nAbstention rate: "
        f"{pct(metrics['abstention']['rate']):.2f}%"
    )

    print(
        f"NOT_APPLICABLE accuracy: "
        f"{pct(metrics['not_applicable']['accuracy']):.2f}%"
    )

    print(
        f"NOT_EVALUATED accuracy: "
        f"{pct(metrics['not_evaluated']['accuracy']):.2f}%"
    )

    print(
        f"\nErrors: {len(report['errors'])}"
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:

    parser = argparse.ArgumentParser(
        description=(
            "Evaluate the frozen DVJ Proposal Reviewer V2 benchmark."
        )
    )

    parser.add_argument(
        "--json-output",
        type=Path,
        default=DEFAULT_JSON_REPORT,
        help="Path for JSON benchmark report.",
    )

    parser.add_argument(
        "--md-output",
        type=Path,
        default=DEFAULT_MD_REPORT,
        help="Path for Markdown benchmark report.",
    )

    args = parser.parse_args()

    # -------------------------------------------------------------------
    # Load and validate
    # -------------------------------------------------------------------

    loaded = validate_and_load()

    # -------------------------------------------------------------------
    # Decision-level dataset
    # -------------------------------------------------------------------

    decisions = build_decisions(loaded)

    expected_decisions = (
        len(PROPOSAL_IDS) * len(RULE_IDS)
    )

    if len(decisions) != expected_decisions:
        raise RuntimeError(
            f"Expected {expected_decisions} decisions, "
            f"got {len(decisions)}"
        )

    # -------------------------------------------------------------------
    # Compute report
    # -------------------------------------------------------------------

    global_metrics = compute_metrics(decisions)

    per_proposal = compute_per_proposal(
        decisions
    )

    engine_breakdown = compute_engine_breakdown(
        decisions
    )

    errors = build_errors(
        decisions
    )

    report = {
        "benchmark": "DVJ Proposal Reviewer V2",
        "benchmark_version": "v2",
        "proposal_count": len(PROPOSAL_IDS),
        "rules_per_proposal": len(RULE_IDS),
        "proposal_ids": PROPOSAL_IDS,
        "rule_ids": RULE_IDS,
        "global_metrics": global_metrics,
        "per_proposal": per_proposal,
        "engine_breakdown": engine_breakdown,
        "errors": errors,
    }

    # -------------------------------------------------------------------
    # Save reports
    # -------------------------------------------------------------------

    save_json(
        report,
        args.json_output,
    )

    markdown = render_markdown(
        report
    )

    args.md_output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    args.md_output.write_text(
        markdown,
        encoding="utf-8",
    )

    # -------------------------------------------------------------------
    # Console
    # -------------------------------------------------------------------

    print_summary(report)

    print("\nReports saved:")

    try:
        json_display = args.json_output.relative_to(ROOT_DIR)
    except ValueError:
        json_display = args.json_output

    try:
        md_display = args.md_output.relative_to(ROOT_DIR)
    except ValueError:
        md_display = args.md_output

    print(f"  JSON -> {json_display}")
    print(f"  MD   -> {md_display}")

    print(
        "\nNo AWS / Bedrock calls were made."
    )


if __name__ == "__main__":
    main()