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
        "status": "COMPLIANT" if checked_phases else "NOT_APPLICABLE",
        "evidence": str(checked_phases) if checked_phases else None,
        "reasoning": (
            "All explicitly stated validation frequencies are at or below "
            "1.5 iterations per week."
            if checked_phases
            else
            "No phase explicitly states validation iterations or feedback "
            "round trips, so the rule is not applicable."
        ),
        "missing_elements": [],
        "recommendation": None,
    }

def check_rule_19(proposal_text: str) -> dict:
    """
    RULE_19:
    The project start date must not fall on a weekend.

    Supports:
    - normalized synthetic proposals:
      "Début potentiel : 21 septembre 2026"
    - extracted real PDFs:
      "4 mai 2026 14 semaines 13 juillet 2026"
    """

    months = {
        "janvier": 1,
        "février": 2,
        "fevrier": 2,
        "mars": 3,
        "avril": 4,
        "mai": 5,
        "juin": 6,
        "juillet": 7,
        "août": 8,
        "aout": 8,
        "septembre": 9,
        "octobre": 10,
        "novembre": 11,
        "décembre": 12,
        "decembre": 12,
    }

    month_pattern = (
        r"janvier|février|fevrier|mars|avril|mai|juin|juillet|"
        r"août|aout|septembre|octobre|novembre|décembre|decembre"
    )

    # ---------------------------------------------------------
    # Strategy 1 — explicit "Début potentiel"
    # Used by normalized/synthetic proposals.
    # ---------------------------------------------------------

    date_match = re.search(
        rf"début\s+(?:d['’]étude\s+)?potentiel(?:le)?\s*:?\s*"
        rf"(\d{{1,2}})\s+"
        rf"({month_pattern})\s+"
        rf"(\d{{4}})",
        proposal_text,
        re.IGNORECASE,
    )

    # ---------------------------------------------------------
    # Strategy 2 — real PDF schedule extraction
    #
    # Example:
    # 4 mai 2026 14 semaines 13 juillet 2026
    # Semaines S1 S2 ...
    #
    # The first date immediately preceding the announced
    # duration is the potential project start date.
    # ---------------------------------------------------------

    if not date_match:
        date_match = re.search(
            rf"(\d{{1,2}})\s+"
            rf"({month_pattern})\s+"
            rf"(\d{{4}})"
            rf"\s+\d+\s+semaines?",
            proposal_text,
            re.IGNORECASE,
        )

    if not date_match:
        return {
            "rule_id": "RULE_19",
            "status": "NON_COMPLIANT",
            "evidence": None,
            "reasoning": (
                "No explicit project start date could be identified."
            ),
            "missing_elements": [
                "Explicit project start date"
            ],
            "recommendation": (
                "Add an explicit project start date."
            ),
        }

    day = int(date_match.group(1))
    month_name = date_match.group(2).lower()
    year = int(date_match.group(3))

    try:
        start_date = datetime(
            year,
            months[month_name],
            day,
        )
    except ValueError:
        return {
            "rule_id": "RULE_19",
            "status": "NON_COMPLIANT",
            "evidence": date_match.group(0),
            "reasoning": (
                "The detected project start date is invalid."
            ),
            "missing_elements": [],
            "recommendation": (
                "Provide a valid project start date."
            ),
        }

    weekday = start_date.strftime("%A")

    evidence = (
        f"Project start date: "
        f"{day:02d}/{months[month_name]:02d}/{year} "
        f"({weekday})"
    )

    if start_date.weekday() >= 5:
        return {
            "rule_id": "RULE_19",
            "status": "NON_COMPLIANT",
            "evidence": evidence,
            "reasoning": (
                "The project start date falls on a weekend."
            ),
            "missing_elements": [],
            "recommendation": (
                "Move the project start date to a weekday."
            ),
        }

    return {
        "rule_id": "RULE_19",
        "status": "COMPLIANT",
        "evidence": evidence,
        "reasoning": (
            "The project start date falls on a weekday."
        ),
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
def check_rule_23(normalized: dict) -> dict:
    methodology_phases = normalized["methodology"]["phases"]
    budget_phases = normalized["budget"]["phases"]

    methodology_jeh = {
        phase["phase_number"]: phase["jeh"]
        for phase in methodology_phases
        if phase.get("phase_number") is not None
        and phase.get("jeh") is not None
    }

    budget_jeh = {
        phase["phase_number"]: phase["jeh"]
        for phase in budget_phases
        if phase.get("phase_number") is not None
        and phase.get("jeh") is not None
    }

    common_phases = sorted(
        set(methodology_jeh) & set(budget_jeh)
    )

    if not common_phases:
        return {
            "rule_id": "RULE_23",
            "status": "NON_COMPLIANT",
            "evidence": None,
            "reasoning": (
                "No comparable phase-level JEH values were found "
                "between methodology and budget."
            ),
            "missing_elements": [
                "Comparable methodology and budget JEH values"
            ],
            "recommendation": (
                "State the JEH count for each phase consistently "
                "in methodology and budget."
            ),
        }

    mismatches = []

    for phase_number in common_phases:
        methodology_value = methodology_jeh[phase_number]
        budget_value = budget_jeh[phase_number]

        if methodology_value != budget_value:
            mismatches.append({
                "phase": phase_number,
                "methodology_jeh": methodology_value,
                "budget_jeh": budget_value,
            })

    evidence = {
        "methodology_jeh": methodology_jeh,
        "budget_jeh": budget_jeh,
        "compared_phases": common_phases,
    }

    if mismatches:
        return {
            "rule_id": "RULE_23",
            "status": "NON_COMPLIANT",
            "evidence": str(evidence),
            "reasoning": (
                f"JEH inconsistencies detected: {mismatches}"
            ),
            "missing_elements": [],
            "recommendation": (
                "Align phase-level JEH counts between methodology "
                "and budget."
            ),
        }

    return {
        "rule_id": "RULE_23",
        "status": "COMPLIANT",
        "evidence": str(evidence),
        "reasoning": (
            "All comparable phase-level JEH counts are consistent "
            "between methodology and budget."
        ),
        "missing_elements": [],
        "recommendation": None,
    }

if __name__ == "__main__":

    from pathlib import Path

    p1 = Path(
        "data/test_proposals/proposal_001.txt"
    ).read_text(encoding="utf-8")

    p2 = Path(
        "data/test_proposals/proposal_002.txt"
    ).read_text(encoding="utf-8")

    print("P001:")
    print(check_rule_19(p1))

    print("\nP002:")
    print(check_rule_19(p2))