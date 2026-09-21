import re
from datetime import datetime
def check_rule_10(normalized: dict) -> dict:
    phases = normalized.get(
        "methodology", {}
    ).get("phases", [])

    if not phases:
        return {
            "rule_id": "RULE_10",
            "status": "NON_COMPLIANT",
            "evidence": None,
            "reasoning": "No methodology phases were found.",
            "missing_elements": ["Methodology phases"],
            "recommendation": (
                "Add a structured methodology with at least "
                "3 steps per phase."
            ),
        }

    phase_counts = []
    violations = []

    for phase in phases:
        phase_number = phase.get("phase_number")
        steps = phase.get("steps") or []

        phase_result = {
            "phase": phase_number,
            "step_count": len(steps),
        }

        phase_counts.append(phase_result)

        if len(steps) < 3:
            violations.append(phase_result)

    evidence = {
        "phase_step_counts": phase_counts
    }

    if violations:
        return {
            "rule_id": "RULE_10",
            "status": "NON_COMPLIANT",
            "evidence": str(evidence),
            "reasoning": (
                "At least one methodology phase contains "
                "fewer than 3 explicit steps: "
                f"{violations}"
            ),
            "missing_elements": [],
            "recommendation": (
                "Add enough explicit steps so that every "
                "methodology phase contains at least 3."
            ),
        }

    return {
        "rule_id": "RULE_10",
        "status": "COMPLIANT",
        "evidence": str(evidence),
        "reasoning": (
            "Every methodology phase contains at least "
            "3 explicit steps."
        ),
        "missing_elements": [],
        "recommendation": None,
    }
def check_rule_13(normalized: dict) -> dict:
    phases = normalized.get(
        "methodology", {}
    ).get("phases", [])

    checked_phases = []
    violations = []

    for phase in phases:
        iterations = phase.get("validation_iterations")
        duration = phase.get("duration_weeks")

        # Rule is conditional:
        # no explicit iterations -> nothing to evaluate.
        if iterations is None:
            continue

        phase_number = phase.get("phase_number")

        if duration is None or duration <= 0:
            violations.append({
                "phase": phase_number,
                "reason": "Duration unavailable",
            })
            continue

        frequency = iterations / duration

        phase_result = {
            "phase": phase_number,
            "iterations": iterations,
            "duration_weeks": duration,
            "iterations_per_week": round(frequency, 2),
        }

        checked_phases.append(phase_result)

        if frequency > 1.5:
            violations.append(phase_result)

    if violations:
        return {
            "rule_id": "RULE_13",
            "status": "NON_COMPLIANT",
            "evidence": str(violations),
            "reasoning": (
                "At least one phase exceeds the maximum "
                "validation frequency of 1.5 iterations per week."
            ),
            "missing_elements": [],
            "recommendation": (
                "Reduce the number of planned validation iterations "
                "or increase the phase duration."
            ),
        }

    if not checked_phases:
        return {
            "rule_id": "RULE_13",
            "status": "NOT_APPLICABLE",
            "evidence": None,
            "reasoning": (
                "No phase explicitly states validation iterations "
                "or feedback round trips."
            ),
            "missing_elements": [],
            "recommendation": None,
        }

    return {
        "rule_id": "RULE_13",
        "status": "COMPLIANT",
        "evidence": str(checked_phases),
        "reasoning": (
            "All explicitly stated validation frequencies are "
            "at or below 1.5 iterations per week."
        ),
        "missing_elements": [],
        "recommendation": None,
    }

def check_rule_19(normalized: dict) -> dict:
    start_date = normalized.get(
        "planning", {}
    ).get("start_date")

    if not start_date:
        return {
            "rule_id": "RULE_19",
            "status": "NON_COMPLIANT",
            "evidence": None,
            "reasoning": "No explicit project start date was found.",
            "missing_elements": ["Project start date"],
            "recommendation": "Specify an explicit project start date.",
        }

    french_months = {
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

    parsed_date = None

    # Formats such as 21/09/2026 or 2026-09-20
    for date_format in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            parsed_date = datetime.strptime(
                start_date,
                date_format,
            )
            break
        except ValueError:
            pass

    # Format such as "4 mai 2026"
    if parsed_date is None:
        match = re.fullmatch(
            r"(\d{1,2})\s+([A-Za-zÀ-ÿ]+)\s+(\d{4})",
            start_date.strip(),
            re.IGNORECASE,
        )

        if match:
            day = int(match.group(1))
            month_name = match.group(2).lower()
            year = int(match.group(3))

            month = french_months.get(month_name)

            if month:
                try:
                    parsed_date = datetime(
                        year,
                        month,
                        day,
                    )
                except ValueError:
                    pass

    if parsed_date is None:
        return {
            "rule_id": "RULE_19",
            "status": "NON_COMPLIANT",
            "evidence": start_date,
            "reasoning": "The project start date could not be parsed.",
            "missing_elements": [],
            "recommendation": (
                "Use an explicit and unambiguous project start date."
            ),
        }

    weekday = parsed_date.strftime("%A")
    is_weekend = parsed_date.weekday() >= 5

    return {
        "rule_id": "RULE_19",
        "status": (
            "NON_COMPLIANT"
            if is_weekend
            else "COMPLIANT"
        ),
        "evidence": (
            f"{parsed_date.strftime('%d/%m/%Y')} "
            f"({weekday})"
        ),
        "reasoning": (
            "The project start date falls on a weekend."
            if is_weekend
            else "The project start date falls on a weekday."
        ),
        "missing_elements": [],
        "recommendation": (
            "Move the project start date to a weekday."
            if is_weekend
            else None
        ),
    }
def check_rule_20(normalized: dict) -> dict:
    planning = normalized.get("planning", {})

    total_duration = planning.get("total_duration_weeks")
    phases = planning.get("phases", [])

    end_weeks = [
        phase.get("end_week")
        for phase in phases
        if phase.get("end_week") is not None
    ]

    if total_duration is None:
        return {
            "rule_id": "RULE_20",
            "status": "NON_COMPLIANT",
            "evidence": None,
            "reasoning": (
                "No explicit total project duration was found "
                "in the planning."
            ),
            "missing_elements": [
                "Explicit total project duration"
            ],
            "recommendation": (
                "State the total project duration explicitly."
            ),
        }

    if not end_weeks:
        return {
            "rule_id": "RULE_20",
            "status": "NON_COMPLIANT",
            "evidence": (
                f"Stated total duration: {total_duration} weeks"
            ),
            "reasoning": (
                "The total duration is stated, but the extracted "
                "planning does not provide enough reliable week-level "
                "information to verify its consistency."
            ),
            "missing_elements": [
                "Verifiable phase timing in planning"
            ],
            "recommendation": (
                "Ensure phase timing is explicitly represented "
                "and consistent with the stated total duration."
            ),
        }

    planning_end_week = max(end_weeks)

    evidence = {
        "stated_total_duration_weeks": total_duration,
        "planning_end_week": planning_end_week,
    }

    if planning_end_week != total_duration:
        return {
            "rule_id": "RULE_20",
            "status": "NON_COMPLIANT",
            "evidence": str(evidence),
            "reasoning": (
                f"The stated project duration is {total_duration} "
                f"weeks, while the planning extends to week "
                f"{planning_end_week}."
            ),
            "missing_elements": [],
            "recommendation": (
                "Align the stated total duration with the "
                "planning timeline."
            ),
        }

    return {
        "rule_id": "RULE_20",
        "status": "COMPLIANT",
        "evidence": str(evidence),
        "reasoning": (
            "The stated total duration is consistent with "
            "the planning timeline."
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
def check_rule_25(normalized: dict) -> dict:
    budget = normalized.get("budget", {})

    project_management_ht = budget.get("project_management_ht")
    total_project_ht = budget.get("total_project_ht")

    if project_management_ht is None or total_project_ht is None:
        return {
            "rule_id": "RULE_25",
            "status": "NON_COMPLIANT",
            "evidence": None,
            "reasoning": (
                "The project management amount or total project "
                "amount could not be identified."
            ),
            "missing_elements": [
                "Project management amount and total project amount"
            ],
            "recommendation": (
                "Explicitly state the project management amount "
                "and total project amount excluding VAT."
            ),
        }

    if total_project_ht <= 0:
        return {
            "rule_id": "RULE_25",
            "status": "NON_COMPLIANT",
            "evidence": str({
                "project_management_ht": project_management_ht,
                "total_project_ht": total_project_ht,
            }),
            "reasoning": "The total project amount is invalid.",
            "missing_elements": [],
            "recommendation": (
                "Provide a valid total project amount excluding VAT."
            ),
        }

    ratio = project_management_ht / total_project_ht
    percentage = ratio * 100

    evidence = {
        "project_management_ht": project_management_ht,
        "total_project_ht": total_project_ht,
        "percentage": round(percentage, 2),
    }

    if 8 <= percentage <= 12:
        return {
            "rule_id": "RULE_25",
            "status": "COMPLIANT",
            "evidence": str(evidence),
            "reasoning": (
                f"Project management represents "
                f"{percentage:.2f}% of the total project amount, "
                "which is within the required 8–12% range."
            ),
            "missing_elements": [],
            "recommendation": None,
        }

    return {
        "rule_id": "RULE_25",
        "status": "NON_COMPLIANT",
        "evidence": str(evidence),
        "reasoning": (
            f"Project management represents "
            f"{percentage:.2f}% of the total project amount, "
            "which is outside the required 8–12% range."
        ),
        "missing_elements": [],
        "recommendation": (
            "Adjust the project management amount so that it "
            "represents between 8% and 12% of the total project amount."
        ),
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