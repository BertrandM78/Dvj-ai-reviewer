import re
from datetime import datetime

def to_float(value):
    """
    Convert a normalized numeric value to float.
    Returns None when conversion is impossible.
    """
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return float(value)

    if isinstance(value, str):
        cleaned = (
            value
            .replace("\u202f", "")
            .replace("\xa0", "")
            .replace(" ", "")
            .replace("€", "")
            .replace(",", ".")
            .strip()
        )

        try:
            return float(cleaned)
        except ValueError:
            return None

    return None

def check_rule_10(normalized: dict) -> dict:
    phases = normalized.get(
        "methodology", {}
    ).get("phases", [])

    if not phases:
        return {
            "rule_id": "RULE_10",
            "status": "NON_COMPLIANT",
            "evidence": None,
            "reasoning": "Aucune phase méthodologique n’a été trouvée.",
            "missing_elements": ["Phases méthodologiques"],
            "recommendation": (
                "Ajoutez une méthodologie structurée comportant au moins "
                "3 étapes par phase."
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
                "Au moins une phase méthodologique comporte "
                "moins de 3 étapes explicites : "
                f"{violations}"
            ),
            "missing_elements": [],
            "recommendation": (
                "Ajoutez suffisamment d’étapes explicites pour que chaque "
                "phase méthodologique en contienne au moins 3."
            ),
        }

    return {
        "rule_id": "RULE_10",
        "status": "COMPLIANT",
        "evidence": str(evidence),
        "reasoning": (
            "Chaque phase méthodologique comporte au moins "
            "3 étapes explicites."
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
                "Au moins une phase dépasse la fréquence maximale "
                "de validation de 1,5 itération par semaine."
            ),
            "missing_elements": [],
            "recommendation": (
                "Réduisez le nombre d’itérations de validation prévues "
                "ou augmentez la durée de la phase."
            ),
        }

    if not checked_phases:
        return {
            "rule_id": "RULE_13",
            "status": "NOT_APPLICABLE",
            "evidence": None,
            "reasoning": (
                "Aucune phase n’indique explicitement le nombre d’itérations "
                "de validation ou de boucles de retour."
            ),
            "missing_elements": [],
            "recommendation": None,
        }

    return {
        "rule_id": "RULE_13",
        "status": "COMPLIANT",
        "evidence": str(checked_phases),
        "reasoning": (
            "Toutes les fréquences de validation indiquées explicitement "
            "sont inférieures ou égales à 1,5 itération par semaine."
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
            "reasoning": "Aucune date explicite de début du projet n’a été trouvée.",
            "missing_elements": ["Date de début du projet"],
            "recommendation": "Indiquez une date explicite de début du projet.",
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
            "reasoning": "La date de début du projet n’a pas pu être analysée.",
            "missing_elements": [],
            "recommendation": (
                "Utilisez une date de début du projet explicite et non ambiguë."
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
            "La date de début du projet tombe un week-end."
            if is_weekend
            else "La date de début du projet tombe un jour ouvré."
        ),
        "missing_elements": [],
        "recommendation": (
            "Déplacez la date de début du projet à un jour ouvré."
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
                "Aucune durée totale explicite du projet n’a été trouvée "
                "dans le planning."
            ),
            "missing_elements": [
                "Durée totale explicite du projet"
            ],
            "recommendation": (
                "Indiquez explicitement la durée totale du projet."
            ),
        }

    if not end_weeks:
        return {
            "rule_id": "RULE_20",
            "status": "NON_COMPLIANT",
            "evidence": (
                f"Durée totale indiquée : {total_duration} semaines"
            ),
            "reasoning": (
                "La durée totale est indiquée, mais le planning extrait "
                "ne fournit pas suffisamment d’informations fiables "
                "au niveau des semaines pour vérifier sa cohérence."
            ),
            "missing_elements": [
                "Calendrier des phases vérifiable dans le planning"
            ],
            "recommendation": (
                "Assurez-vous que le calendrier des phases est représenté "
                "explicitement et cohérent avec la durée totale indiquée."
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
                f"La durée du projet indiquée est de {total_duration} "
                f"semaines, tandis que le planning s’étend jusqu’à la semaine "
                f"{planning_end_week}."
            ),
            "missing_elements": [],
            "recommendation": (
                "Alignez la durée totale indiquée sur le calendrier "
                "du planning."
            ),
        }

    return {
        "rule_id": "RULE_20",
        "status": "COMPLIANT",
        "evidence": str(evidence),
        "reasoning": (
            "La durée totale indiquée est cohérente avec "
            "le calendrier du planning."
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
                "Aucune valeur de JEH comparable au niveau des phases "
                "n’a été trouvée entre la méthodologie et le budget."
            ),
            "missing_elements": [
                "Valeurs de JEH comparables entre la méthodologie et le budget"
            ],
            "recommendation": (
                "Indiquez le nombre de JEH de chaque phase de manière cohérente "
                "dans la méthodologie et le budget."
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
                f"Incohérences de JEH détectées : {mismatches}"
            ),
            "missing_elements": [],
            "recommendation": (
                "Alignez les nombres de JEH par phase entre la méthodologie "
                "et le budget."
            ),
        }

    return {
        "rule_id": "RULE_23",
        "status": "COMPLIANT",
        "evidence": str(evidence),
        "reasoning": (
            "Tous les nombres de JEH comparables par phase sont cohérents "
            "entre la méthodologie et le budget."
        ),
        "missing_elements": [],
        "recommendation": None,
    }
def check_rule_25(normalized: dict) -> dict:
    budget = normalized.get("budget", {})

    project_management_ht = to_float(budget.get("project_management_ht"))
    total_project_ht = to_float(budget.get("total_project_ht"))

    if project_management_ht is None or total_project_ht is None:
        return {
            "rule_id": "RULE_25",
            "status": "NON_COMPLIANT",
            "evidence": None,
            "reasoning": (
                "Le montant de la gestion de projet ou le montant total "
                "du projet n’a pas pu être identifié."
            ),
            "missing_elements": [
                "Montant de la gestion de projet et montant total du projet"
            ],
            "recommendation": (
                "Indiquez explicitement le montant de la gestion de projet "
                "et le montant total du projet hors TVA."
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
            "reasoning": "Le montant total du projet est invalide.",
            "missing_elements": [],
            "recommendation": (
                "Indiquez un montant total valide pour le projet hors TVA."
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
                f"La gestion de projet représente "
                f"{percentage:.2f}% du montant total du projet, "
                f"ce qui est dans la plage requise de 8 à 12%."
            ),
            "missing_elements": [],
            "recommendation": None,
        }

    return {

        "rule_id": "RULE_25",
        "status": "NON_COMPLIANT",
        "reason": (
            f"La gestion de projet représente {percentage:.2f}% "
            "du montant total du projet, ce qui est en dehors "
            "de la plage requise de 8 à 12%."
        ),
        "evidence": {
            "project_management_ht": project_management_ht,
            "total_project_ht": total_project_ht,
            "percentage": round(percentage, 2),
        },
        "recommendation": (
            "Ajuster le montant de la gestion de projet afin "
            "qu'il représente entre 8% et 12% du montant total du projet."
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