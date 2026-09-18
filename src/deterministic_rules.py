import re
from datetime import datetime

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

def check_rule_19(proposal_text: str) -> dict:
    """
    RULE_19:
    The project start date must not fall on a weekend.
    """

    months = {
        "janvier": 1,
        "février": 2,
        "mars": 3,
        "avril": 4,
        "mai": 5,
        "juin": 6,
        "juillet": 7,
        "août": 8,
        "septembre": 9,
        "octobre": 10,
        "novembre": 11,
        "décembre": 12,
    }

    date_match = re.search(
        r"début\s+potentiel\s*:\s*"
        r"(\d{1,2})\s+"
        r"(janvier|février|mars|avril|mai|juin|juillet|août|"
        r"septembre|octobre|novembre|décembre)\s+"
        r"(\d{4})",
        proposal_text,
        re.IGNORECASE,
    )

    if not date_match:
        return {
            "rule_id": "RULE_19",
            "stadate_matus": "NON_COMPLIANT",
            "evidence": None,
            "reasoning": "No explicit project start date could be identified.",
            "missing_elements": ["Explicit project start date"],
            "recommendation": "Add an explicit project start date.",
        }

    day = int(date_match.group(1))
    month_name = date_match.group(2).lower()
    year = int(date_match.group(3))

    start_date = datetime(
        year,
        months[month_name],
        day,
    )

    weekday = start_date.strftime("%A")

    if start_date.weekday() >= 5:
        return {
            "rule_id": "RULE_19",
            "status": "NON_COMPLIANT",
            "evidence": (
                f"Project start date: {day:02d}/"
                f"{months[month_name]:02d}/{year} ({weekday})"
            ),
            "reasoning": "The project start date falls on a weekend.",
            "missing_elements": [],
            "recommendation": (
                "Move the project start date to a weekday."
            ),
        }

    return {
        "rule_id": "RULE_19",
        "status": "COMPLIANT",
        "evidence": (
            f"Project start date: {day:02d}/"
            f"{months[month_name]:02d}/{year} ({weekday})"
        ),
        "reasoning": "The project start date falls on a weekday.",
        "missing_elements": [],
        "recommendation": None,
    }
def check_rule_20(proposal_text: str) -> dict:
    """
    RULE_20:
    The announced total project duration must be coherent
    with the project schedule.
    """

    # Isolate the schedule section
    schedule_match = re.search(
        r"(SLIDE\s+\d+\s+—\s+ÉCHÉANCIER.*?)(?=SLIDE\s+\d+\s+—|$)",
        proposal_text,
        re.DOTALL | re.IGNORECASE,
    )

    if not schedule_match:
        return {
            "rule_id": "RULE_20",
            "status": "NON_COMPLIANT",
            "evidence": None,
            "reasoning": "No project schedule section could be identified.",
            "missing_elements": ["Project schedule"],
            "recommendation": (
                "Add a clearly identified project schedule with "
                "an announced total duration."
            ),
        }

    schedule_text = schedule_match.group(1)

    # Extract announced total duration
    duration_match = re.search(
        r"Durée\s+totale\s+annoncée\s*:\s*(\d+)\s+semaines?",
        schedule_text,
        re.IGNORECASE,
    )

    if not duration_match:
        return {
            "rule_id": "RULE_20",
            "status": "NON_COMPLIANT",
            "evidence": None,
            "reasoning": "No announced total project duration could be identified.",
            "missing_elements": ["Announced total project duration"],
            "recommendation": "Add an explicit total project duration.",
        }

    announced_duration = int(duration_match.group(1))

    # Accept both:
    # S1 à S2
    # Semaine 1 à semaine 2
    week_ranges = re.findall(
        r"(?:S|Semaine\s+)(\d+)\s+à\s+(?:S|semaine\s+)(\d+)",
        schedule_text,
        re.IGNORECASE,
    )

    if not week_ranges:
        return {
            "rule_id": "RULE_20",
            "status": "NON_COMPLIANT",
            "evidence": None,
            "reasoning": "No phase week ranges could be identified in the schedule.",
            "missing_elements": ["Phase week ranges"],
            "recommendation": (
                "Specify the start and end weeks for each project phase."
            ),
        }

    # The actual schedule duration is determined by the latest
    # explicitly scheduled week.
    latest_week = max(int(end_week) for _, end_week in week_ranges)

    if announced_duration != latest_week:
        return {
            "rule_id": "RULE_20",
            "status": "NON_COMPLIANT",
            "evidence": (
                f"Announced duration: {announced_duration} weeks; "
                f"schedule extends to week {latest_week}."
            ),
            "reasoning": (
                "The announced total project duration is inconsistent "
                "with the latest week shown in the schedule."
            ),
            "missing_elements": [],
            "recommendation": (
                "Align the announced total duration with the project schedule."
            ),
        }

    return {
        "rule_id": "RULE_20",
        "status": "COMPLIANT",
        "evidence": (
            f"Announced duration: {announced_duration} weeks; "
            f"schedule extends to week {latest_week}."
        ),
        "reasoning": (
            "The announced total project duration is consistent "
            "with the project schedule."
        ),
        "missing_elements": [],
        "recommendation": None,
    }

if __name__ == "__main__":

    from pathlib import Path

    p1 = Path("data/test_proposals/proposal_001.txt").read_text()
    p2 = Path("data/test_proposals/proposal_002.txt").read_text()

    print(check_rule_20(p1))
    print(check_rule_20(p2))