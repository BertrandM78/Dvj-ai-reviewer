import json
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

GROUND_TRUTH_PATH = Path(
    "data/evaluation/ground_truth.json"
)

RESULTS_DIR = Path(
    "data/results"
)


# ============================================================
# LOAD DATA
# ============================================================

def load_json(file_path: Path) -> dict:
    """
    Load a JSON file and return its content as a Python dictionary.
    """

    with file_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


# ============================================================
# NORMALIZE LLM PREDICTIONS
# ============================================================

def extract_predictions(review_data: dict) -> dict:
    """
    Convert the LLM review structure:

    {
        "results": [
            {
                "rule_id": "RULE_1",
                "status": "NON_COMPLIANT"
            },
            ...
        ]
    }

    into:

    {
        "RULE_1": "NON_COMPLIANT",
        ...
    }

    This makes comparison with the ground truth easier.
    """

    predictions = {}

    for result in review_data.get(
        "results",
        []
    ):
        rule_id = result.get("rule_id")
        status = result.get("status")

        if rule_id is not None and status is not None:
            predictions[rule_id] = status

    return predictions


# ============================================================
# EVALUATION
# ============================================================

def evaluate() -> None:
    """
    Compare all saved LLM predictions against the human-defined
    ground truth and calculate classification metrics.

    NON_COMPLIANT is considered the positive class because
    violations are what the reviewer is designed to detect.
    """

    ground_truth = load_json(
        GROUND_TRUTH_PATH
    )

    # Global counters
    correct = 0
    total = 0

    true_positive = 0
    false_positive = 0
    false_negative = 0

    print(
        "\n========================================"
    )
    print(
        "DVJ AI PROPOSAL REVIEWER — EVALUATION"
    )
    print(
        "========================================"
    )

    # --------------------------------------------------------
    # Evaluate each proposal
    # --------------------------------------------------------

    for proposal_id, expected_rules in ground_truth.items():

        print(
            f"\n--- {proposal_id} ---"
        )

        review_path = (
            RESULTS_DIR
            / f"{proposal_id}_review.json"
        )

        # Make sure a prediction exists.
        if not review_path.exists():
            print(
                f"ERROR: Missing review file: {review_path}"
            )
            continue

        review_data = load_json(
            review_path
        )

        predicted_rules = extract_predictions(
            review_data
        )

        # ----------------------------------------------------
        # Compare every expected rule
        # ----------------------------------------------------

        for rule_id, expected_status in expected_rules.items():

            predicted_status = predicted_rules.get(
                rule_id
            )

            # The LLM failed to return this rule.
            if predicted_status is None:

                print(
                    f"✗ {rule_id} | "
                    f"expected={expected_status} | "
                    f"predicted=MISSING"
                )

                total += 1

                # If the missing prediction was actually
                # a violation, the system failed to detect it.
                if expected_status == "NON_COMPLIANT":
                    false_negative += 1

                continue

            # ------------------------------------------------
            # Accuracy
            # ------------------------------------------------

            is_correct = (
                predicted_status == expected_status
            )

            total += 1

            if is_correct:
                correct += 1

            symbol = (
                "✓"
                if is_correct
                else "✗"
            )

            print(
                f"{symbol} {rule_id} | "
                f"expected={expected_status} | "
                f"predicted={predicted_status}"
            )

            # ------------------------------------------------
            # Precision / Recall
            #
            # Positive class = NON_COMPLIANT
            # ------------------------------------------------

            if (
                expected_status == "NON_COMPLIANT"
                and predicted_status == "NON_COMPLIANT"
            ):
                true_positive += 1

            elif (
                expected_status == "COMPLIANT"
                and predicted_status == "NON_COMPLIANT"
            ):
                false_positive += 1

            elif (
                expected_status == "NON_COMPLIANT"
                and predicted_status == "COMPLIANT"
            ):
                false_negative += 1

    # ========================================================
    # GLOBAL METRICS
    # ========================================================

    accuracy = (
        correct / total
        if total > 0
        else 0
    )

    precision_denominator = (
        true_positive
        + false_positive
    )

    precision = (
        true_positive / precision_denominator
        if precision_denominator > 0
        else 0
    )

    recall_denominator = (
        true_positive
        + false_negative
    )

    recall = (
        true_positive / recall_denominator
        if recall_denominator > 0
        else 0
    )

    # ========================================================
    # DISPLAY RESULTS
    # ========================================================

    print(
        "\n========================================"
    )
    print(
        "GLOBAL RESULTS"
    )
    print(
        "========================================"
    )

    print(
        f"Correct classifications: {correct}/{total}"
    )

    print(
        f"Rule accuracy:          {accuracy:.1%}"
    )

    print(
        f"Violation precision:    {precision:.1%}"
    )

    print(
        f"Violation recall:       {recall:.1%}"
    )

    print(
        "\nConfusion counts:"
    )

    print(
        f"True positives:         {true_positive}"
    )

    print(
        f"False positives:        {false_positive}"
    )

    print(
        f"False negatives:        {false_negative}"
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    evaluate()