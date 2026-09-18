import re


def check_rule_10(proposal_text: str) -> dict:
    """
    RULE_10:
    Each methodology phase must contain at least 3 explicit steps/bullets.
    """

    # Only analyze methodology sections.
    # Stop before the next major section after methodology.
    methodology_match = re.search(
        r"(SLIDE\s+\d+\s+—\s+NOTRE MÉTHODOLOGIE.*?)(?="
        r"SLIDE\s+\d+\s+—\s+(?!NOTRE MÉTHODOLOGIE)|$)",
        proposal_text,
        re.DOTALL | re.IGNORECASE,
    )

    if not methodology_match:
        return {
            "rule_id": "RULE_10",
            "status": "NON_COMPLIANT",
            "evidence": None,
            "reasoning": "No methodology section could be identified.",
            "missing_elements": [
                "Methodology section with phases and explicit steps"
            ],
            "recommendation": (
                "Add a clearly identified methodology section containing "
                "at least 3 explicit steps for each phase."
            ),
        }

    methodology_text = methodology_match.group(1)

    # Extract each phase inside the methodology section.
    phase_pattern = re.compile(
        r"(PHASE\s+(\d+)\s+—.*?)(?=PHASE\s+\d+\s+—|"
        r"SLIDE\s+\d+\s+—|$)",
        re.DOTALL | re.IGNORECASE,
    )

    phases = phase_pattern.findall(methodology_text)

    checked_phases = []
    violations = []

    for phase_text, phase_number in phases:

        # Steps in our normalized proposals are represented as:
        # - First step
        # - Second step
        # - Third step
        steps = re.findall(
            r"^\s*-\s+\S.*$",
            phase_text,
            re.MULTILINE,
        )

        step_count = len(steps)

        checked_phases.append(
            {
                "phase": phase_number,
                "step_count": step_count,
            }
        )

        if step_count < 3:
            violations.append(
                f"Phase {phase_number} contains only "
                f"{step_count} explicit steps."
            )

    if violations:
        return {
            "rule_id": "RULE_10",
            "status": "NON_COMPLIANT",
            "evidence": "; ".join(violations),
            "reasoning": (
                "At least one methodology phase contains fewer "
                "than the required 3 explicit steps."
            ),
            "missing_elements": [
                "At least 3 explicit steps are required in each methodology phase"
            ],
            "recommendation": (
                "Add enough explicit steps to each non-compliant methodology "
                "phase so that every phase contains at least 3."
            ),
        }

    return {
        "rule_id": "RULE_10",
        "status": "COMPLIANT",
        "evidence": str(checked_phases),
        "reasoning": (
            "Every detected methodology phase contains at least "
            "3 explicit steps."
        ),
        "missing_elements": [],
        "recommendation": None,
    }


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

    p1 = Path("data/test_proposals/proposal_001.txt").read_text()
    p2 = Path("data/test_proposals/proposal_002.txt").read_text()

    print(check_rule_10(p1))
    print(check_rule_10(p2))