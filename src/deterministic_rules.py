import re


def check_rule_13(proposal_text: str) -> dict:
    """
    RULE_13 — Validation iterations.

    When a phase requires client validation/feedback:
    - the number of iterations must be explicit;
    - the ratio must not exceed 1.5 iterations per week.
    """

    # Find methodology phases.
    phase_pattern = re.compile(
        r"(PHASE\s+\d+\s+—.*?)(?=PHASE\s+\d+\s+—|SLIDE\s+\d+|$)",
        re.DOTALL | re.IGNORECASE,
    )

    phases = phase_pattern.findall(proposal_text)

    violations = []
    checked_phases = []

    for phase in phases:

        weeks_match = re.search(
            r"(\d+)\s+semaines?",
            phase,
            re.IGNORECASE,
        )

        iterations_match = re.search(
            r"(\d+)\s+allers?-retours?",
            phase,
            re.IGNORECASE,
        )

        # No explicit validation iterations:
        # this phase does not provide evidence that the
        # validation-frequency requirement is triggered.
        if not iterations_match:
            continue

        if not weeks_match:
            violations.append(
                "Validation iterations are specified but phase duration "
                "could not be determined."
            )
            continue

        weeks = int(weeks_match.group(1))
        iterations = int(iterations_match.group(1))

        ratio = iterations / weeks

        checked_phases.append(
            {
                "weeks": weeks,
                "iterations": iterations,
                "ratio": ratio,
            }
        )

        if ratio > 1.5:
            violations.append(
                f"{iterations} validation iterations over {weeks} weeks "
                f"= {ratio:.2f} iterations/week."
            )

    if violations:
        return {
            "rule_id": "RULE_13",
            "status": "NON_COMPLIANT",
            "evidence": "; ".join(violations),
            "reasoning": (
                "At least one phase exceeds the maximum validation "
                "frequency of 1.5 iterations per week."
            ),
            "missing_elements": [
                "Validation frequency exceeds the permitted threshold"
            ],
            "recommendation": (
                "Reduce the number of validation iterations so that "
                "each relevant phase stays at or below 1.5 iterations "
                "per week."
            ),
        }

    return {
        "rule_id": "RULE_13",
        "status": "COMPLIANT",
        "evidence": str(checked_phases) if checked_phases else None,
        "reasoning": (
            "No explicitly stated validation frequency exceeds "
            "1.5 iterations per week."
        ),
        "missing_elements": [],
        "recommendation": None,
    }

if __name__ == "__main__":

    from pathlib import Path

    for proposal_name in [
        "proposal_001.txt",
        "proposal_002.txt",
    ]:

        proposal_path = (
            Path("data/test_proposals")
            / proposal_name
        )

        proposal_text = proposal_path.read_text(
            encoding="utf-8"
        )

        result = check_rule_13(proposal_text)

        print(f"\n--- {proposal_name} ---")
        print(result)