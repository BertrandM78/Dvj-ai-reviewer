from typing import Callable
from src.rules.loader import load_rules, get_rules_by_engine
import re
import calendar
import unicodedata
from difflib import SequenceMatcher

RuleResult = dict
RuleFunction = Callable[[dict, dict], RuleResult]

def normalize_title(value: str | None) -> str:
    if not value:
        return ""

    value = unicodedata.normalize(
        "NFKD",
        value,
    )

    value = "".join(
        char
        for char in value
        if not unicodedata.combining(char)
    )

    value = value.lower()

    value = re.sub(
        r"[^a-z0-9]+",
        " ",
        value,
    )

    return " ".join(value.split())


def titles_are_close(
    actual: str | None,
    expected: str | None,
    threshold: float = 0.80,
) -> bool:
    actual_normalized = normalize_title(actual)
    expected_normalized = normalize_title(expected)

    if not actual_normalized or not expected_normalized:
        return False

    if actual_normalized == expected_normalized:
        return True

    similarity = SequenceMatcher(
        None,
        actual_normalized,
        expected_normalized,
    ).ratio()

    return similarity >= threshold


def has_content(value) -> bool:
    if value is None:
        return False

    if isinstance(value, str):
        return bool(value.strip())

    if isinstance(value, list):
        return len(value) > 0

    if isinstance(value, dict):
        return any(
            has_content(item)
            for item in value.values()
        )

    return True

def make_result(
    rule: dict,
    status: str,
    reason: str,
    evidence: str | None = None,
    recommendation: str | None = None,
) -> dict:
    """Build a standardized V2 rule result."""

    return {
        "rule_id": rule["id"],
        "title": rule["title"],
        "section": rule["section"],
        "type": rule["type"],
        "dimension": rule["dimension"],
        "severity": rule["severity"],
        "status": status,
        "reason": reason,
        "evidence": evidence,
        "recommendation": recommendation,
    }


def not_evaluated(
    rule: dict,
    reason: str,
) -> dict:
    return make_result(
        rule=rule,
        status="NOT_EVALUATED",
        reason=reason,
    )

RULE_HANDLERS: dict[str, RuleFunction] = {}


def register(rule_id: str):
    """Register a deterministic rule handler."""

    def decorator(function: RuleFunction):
        RULE_HANDLERS[rule_id] = function
        return function

    return decorator


from datetime import date

@register("RULE_001")
def check_required_structure(document, rule):
    slides = document.get("slides", [])

    missing_items = []
    found_items = []

    # Required slides
    for requirement in rule.get(
        "required_slides",
        [],
    ):
        expected_title = requirement["title"]
        match_type = requirement["match"]

        found = False

        if match_type == "SEMANTIC":
            expected_section = requirement.get(
                "detected_section"
            )

            if expected_section:
                found = any(
                    slide.get("detected_section")
                    == expected_section
                    for slide in slides
                )

        elif match_type == "EXACT_OR_CLOSE":
            found = any(
                titles_are_close(
                    slide.get("title"),
                    expected_title,
                )
                for slide in slides
            )

        else:
            return not_evaluated(
                rule,
                (
                    "Mode de correspondance inconnu "
                    f"pour « {expected_title} » : "
                    f"{match_type}"
                ),
            )

        if found:
            found_items.append(expected_title)
        else:
            missing_items.append(expected_title)

    # Required semantic sections
    for requirement in rule.get(
        "required_sections",
        [],
    ):
        title = requirement["title"]
        normalized_field = requirement.get(
            "normalized_field"
        )

        if not normalized_field:
            return not_evaluated(
                rule,
                (
                    "Impossible d'évaluer la section "
                    f"« {title} » : normalized_field absent."
                ),
            )

        value = document.get(
            normalized_field
        )

        if has_content(value):
            found_items.append(title)
        else:
            missing_items.append(title)

    if missing_items:
        return make_result(
            rule,
            "NON_COMPLIANT",
            (
                "Certaines slides ou sections "
                "obligatoires sont absentes."
            ),
            evidence=(
                "Éléments manquants : "
                + "; ".join(missing_items)
                + ". Éléments détectés : "
                + "; ".join(found_items)
                + "."
            ),
            recommendation=(
                "Ajouter ou renommer les éléments "
                "obligatoires manquants."
            ),
        )

    return make_result(
        rule,
        "COMPLIANT",
        (
            "Toutes les slides et sections "
            "obligatoires sont présentes."
        ),
        evidence=(
            "Éléments détectés : "
            + "; ".join(found_items)
            + "."
        ),
    )

@register("RULE_019")
def check_project_start_date(
    document: dict,
    rule: dict,
) -> dict:

    start_date = (
        document
        .get("planning", {})
        .get("project_start_date")
    )

    if not start_date:
        return not_evaluated(
            rule,
            "La date de début du projet n'a pas pu être extraite.",
        )

    try:
        parsed_date = date.fromisoformat(start_date)
    except (TypeError, ValueError):
        return not_evaluated(
            rule,
            "La date de début extraite n'est pas exploitable.",
        )

    weekday = parsed_date.weekday()

    if weekday >= 5:
        return make_result(
            rule=rule,
            status="NON_COMPLIANT",
            reason="La date de début du projet tombe un week-end.",
            evidence=f"Date de début : {start_date}",
            recommendation=(
                "Déplacer le début de la mission sur un jour ouvré."
            ),
        )

    return make_result(
        rule=rule,
        status="COMPLIANT",
        reason="La date de début du projet est un jour de semaine.",
        evidence=f"Date de début : {start_date}",
    )

@register("RULE_022")
def check_project_management_ratio(
    document: dict,
    rule: dict,
) -> dict:

    budget = document.get("budget", {})

    project_management_ht = budget.get(
        "project_management_ht"
    )
    total_ht = budget.get("total_ht")

    if project_management_ht is None or total_ht is None:
        return not_evaluated(
            rule,
            "Les montants nécessaires au calcul sont absents.",
        )

    if total_ht <= 0:
        return not_evaluated(
            rule,
            "Le budget total HT n'est pas exploitable.",
        )

    parameters = rule.get("parameters", {})

    min_percentage = parameters.get("min_percentage")
    max_percentage = parameters.get("max_percentage")

    if min_percentage is None or max_percentage is None:
        return not_evaluated(
            rule,
            "Les seuils de gestion de projet ne sont pas configurés.",
        )

    ratio = project_management_ht / total_ht * 100

    evidence = (
        f"Gestion de projet : {project_management_ht:.2f} € HT ; "
        f"total : {total_ht:.2f} € HT ; "
        f"part : {ratio:.1f} %."
    )

    if min_percentage <= ratio <= max_percentage:
        return make_result(
            rule=rule,
            status="COMPLIANT",
            reason=(
                "La part de gestion de projet respecte "
                "la plage attendue."
            ),
            evidence=evidence,
        )

    return make_result(
        rule=rule,
        status="NON_COMPLIANT",
        reason=(
            "La part de gestion de projet est en dehors "
            "de la plage attendue."
        ),
        evidence=evidence,
        recommendation=(
            f"Vérifier que la gestion de projet représente "
            f"entre {min_percentage} % et "
            f"{max_percentage} % du total HT."
        ),
    )

@register("RULE_028")
def check_project_manager_experience(
    document: dict,
    rule: dict,
) -> dict:

    budget = document.get("budget", {})
    team = document.get("team", {})

    total_ht = budget.get("total_ht")

    parameters = rule.get("parameters", {})

    budget_threshold = parameters.get(
        "budget_threshold_ht"
    )
    minimum_missions = parameters.get(
        "minimum_previous_missions"
    )

    if total_ht is None:
        return not_evaluated(
            rule,
            "Le budget total HT n'a pas pu être extrait.",
        )

    if budget_threshold is None or minimum_missions is None:
        return not_evaluated(
            rule,
            "Les paramètres de la règle ne sont pas configurés.",
        )

    # Conditional rule
    if total_ht <= budget_threshold:
        return make_result(
            rule=rule,
            status="NOT_APPLICABLE",
            reason=(
                f"Le budget total HT ne dépasse pas "
                f"{budget_threshold} €."
            ),
            evidence=f"Budget total : {total_ht:.2f} € HT.",
        )

    project_manager = team.get("project_manager")

    if not project_manager:
        return make_result(
            rule=rule,
            status="NON_COMPLIANT",
            reason=(
                "Aucun chef de projet identifiable "
                "n'a été extrait."
            ),
            recommendation=(
                "Identifier explicitement le chef de projet."
            ),
        )

    mission_count = project_manager.get("mission_count")

    if mission_count is None:
        return not_evaluated(
            rule,
            (
                "Le nombre de missions précédentes du "
                "chef de projet n'est pas disponible."
            ),
        )

    if mission_count >= minimum_missions:
        return make_result(
            rule=rule,
            status="COMPLIANT",
            reason=(
                "Le chef de projet dispose du nombre "
                "minimum de missions requis."
            ),
            evidence=(
                f"{mission_count} mission(s) précédente(s) ; "
                f"minimum requis : {minimum_missions}."
            ),
        )

    return make_result(
        rule=rule,
        status="NON_COMPLIANT",
        reason=(
            "Le chef de projet ne dispose pas du nombre "
            "minimum de missions requis."
        ),
        evidence=(
            f"{mission_count} mission(s) précédente(s) ; "
            f"minimum requis : {minimum_missions}."
        ),
        recommendation=(
            "Affecter un chef de projet disposant de "
            "l'expérience minimale requise."
        ),
    )

def run_deterministic_rules(
    normalized_document: dict,
    rules: list[dict] | None = None,
) -> list[dict]:

    if rules is None:
        rules = load_rules()

    deterministic_rules = get_rules_by_engine(
        rules,
        "DETERMINISTIC",
    )

    document = normalized_document.get(
        "document",
        normalized_document,
    )

    results = []

    for rule in deterministic_rules:
        handler = RULE_HANDLERS.get(rule["id"])

        if handler is None:
            results.append(
                not_evaluated(
                    rule,
                    "Cette règle déterministe n'est pas encore implémentée.",
                )
            )
            continue

        try:
            result = handler(document, rule)
        except Exception as error:
            result = not_evaluated(
                rule,
                f"Erreur lors de l'évaluation : {error}",
            )

        results.append(result)

    return results

@register("RULE_002")
def check_proposal_reference(
    document: dict,
    rule: dict,
) -> dict:

    metadata = document.get("metadata", {})

    reference = metadata.get("proposal_reference")
    proposal_date = metadata.get("proposal_date")

    # 1. La référence doit exister
    if not reference:
        return make_result(
            rule=rule,
            status="NON_COMPLIANT",
            reason="La référence de la proposition est absente.",
            recommendation=(
                "Ajouter une référence au format "
                "DE-MMYY-XXXX-XXXX-XXXX."
            ),
        )

    # 2. Nettoyage des espaces issus de l'extraction PDF
    normalized_reference = re.sub(
        r"\s+",
        "",
        reference.upper(),
    )

    # 3. Vérification du format
    pattern = r"^DE-(\d{4})-\d{4}-\d{4}-\d{4}$"

    match = re.match(pattern, normalized_reference)

    if not match:
        return make_result(
            rule=rule,
            status="NON_COMPLIANT",
            reason=(
                "La référence ne respecte pas le format attendu."
            ),
            evidence=f"Référence : {reference}",
            recommendation=(
                "Utiliser le format DE-MMYY-XXXX-XXXX-XXXX."
            ),
        )

    reference_mmyy = match.group(1)

    # 4. Sans date de proposition, impossible de vérifier MMYY
    if not proposal_date:
        return not_evaluated(
            rule,
            (
                "Le format de la référence est valide, mais "
                "la date de proposition n'a pas pu être extraite ; "
                "la cohérence MMYY ne peut donc pas être vérifiée."
            ),
        )

    # 5. Vérification MMYY ↔ date de proposition
    try:
        parsed_date = date.fromisoformat(proposal_date)
    except (TypeError, ValueError):
        return not_evaluated(
            rule,
            "La date de proposition n'est pas exploitable.",
        )

    expected_mmyy = (
        f"{parsed_date.month:02d}"
        f"{str(parsed_date.year)[-2:]}"
    )

    if reference_mmyy != expected_mmyy:
        return make_result(
            rule=rule,
            status="NON_COMPLIANT",
            reason=(
                "Le mois et l'année de la référence "
                "ne correspondent pas à la date "
                "de la proposition."
            ),
            evidence=(
                f"Référence : {reference} ; "
                f"date : {proposal_date}."
            ),
            recommendation=(
                f"Utiliser MMYY = {expected_mmyy}."
            ),
        )

    # 6. Format + cohérence temporelle validés
    return make_result(
        rule=rule,
        status="COMPLIANT",
        reason=(
            "La référence respecte le format attendu "
            "et est cohérente avec la date."
        ),
        evidence=(
            f"Référence : {reference} ; "
            f"date : {proposal_date}."
        ),
    )

def add_one_calendar_month(value: date) -> date:
    if value.month == 12:
        year = value.year + 1
        month = 1
    else:
        year = value.year
        month = value.month + 1

    last_day = calendar.monthrange(
        year,
        month,
    )[1]

    day = min(value.day, last_day)

    return date(year, month, day)

@register("RULE_003")
def check_validity_date(
    document: dict,
    rule: dict,
) -> dict:

    metadata = document.get("metadata", {})

    proposal_date = metadata.get("proposal_date")
    validity_date = metadata.get("validity_date")

    if not proposal_date:
        return not_evaluated(
            rule,
            "La date de proposition n'a pas pu être extraite.",
        )

    if not validity_date:
        return make_result(
            rule=rule,
            status="NON_COMPLIANT",
            reason="La date de validité est absente.",
            recommendation=(
                "Ajouter une date de validité située "
                "exactement un mois calendaire après "
                "la date de proposition."
            ),
        )

    try:
        proposal = date.fromisoformat(proposal_date)
        validity = date.fromisoformat(validity_date)
    except (TypeError, ValueError):
        return not_evaluated(
            rule,
            "Une des dates extraites n'est pas exploitable.",
        )

    expected = add_one_calendar_month(proposal)

    if validity != expected:
        return make_result(
            rule=rule,
            status="NON_COMPLIANT",
            reason=(
                "La date de validité n'est pas située "
                "exactement un mois calendaire après "
                "la date de proposition."
            ),
            evidence=(
                f"Proposition : {proposal_date} ; "
                f"validité : {validity_date} ; "
                f"attendu : {expected.isoformat()}."
            ),
            recommendation=(
                f"Utiliser la date de validité "
                f"{expected.isoformat()}."
            ),
        )

    return make_result(
        rule=rule,
        status="COMPLIANT",
        reason="La date de validité est correcte.",
        evidence=(
            f"Proposition : {proposal_date} ; "
            f"validité : {validity_date}."
        ),
    )

@register("RULE_009")
def check_methodology_step_count(
    document: dict,
    rule: dict,
) -> dict:

    phases = (
        document
        .get("methodology", {})
        .get("phases", [])
    )

    if not phases:
        return not_evaluated(
            rule,
            "Aucune phase méthodologique n'a pu être extraite.",
        )

    parameters = rule.get("parameters", {})
    minimum_steps = parameters.get("minimum_steps_per_phase", 3)

    invalid_phases = []

    for phase in phases:
        steps = phase.get("steps") or []

        if len(steps) < minimum_steps:
            invalid_phases.append(
                {
                    "number": phase.get("number"),
                    "title": phase.get("title"),
                    "count": len(steps),
                }
            )

    if invalid_phases:
        evidence = "; ".join(
            (
                f"Phase {phase['number']} "
                f"« {phase['title']} » : "
                f"{phase['count']} étape(s)"
            )
            for phase in invalid_phases
        )

        return make_result(
            rule=rule,
            status="NON_COMPLIANT",
            reason=(
                "Certaines phases ne contiennent pas "
                f"au moins {minimum_steps} étapes."
            ),
            evidence=evidence,
            recommendation=(
                f"Détailler chaque phase avec au moins "
                f"{minimum_steps} étapes méthodologiques."
            ),
        )

    return make_result(
        rule=rule,
        status="COMPLIANT",
        reason=(
            f"Toutes les phases contiennent au moins "
            f"{minimum_steps} étapes."
        ),
    )

@register("RULE_010")
def check_phase_required_information(
    document: dict,
    rule: dict,
) -> dict:

    phases = (
        document
        .get("methodology", {})
        .get("phases", [])
    )

    if not phases:
        return not_evaluated(
            rule,
            "Aucune phase méthodologique n'a pu être extraite.",
        )

    required_fields = {
        "duration_weeks": "durée",
        "jeh": "nombre de JEH",
        "price_ht": "prix HT",
    }

    invalid_phases = []

    for phase in phases:
        missing = [
            label
            for field, label in required_fields.items()
            if phase.get(field) is None
        ]

        if missing:
            invalid_phases.append(
                {
                    "number": phase.get("number"),
                    "title": phase.get("title"),
                    "missing": missing,
                }
            )

    if invalid_phases:
        evidence = "; ".join(
            (
                f"Phase {phase['number']} "
                f"« {phase['title']} » : "
                f"{', '.join(phase['missing'])} manquant(s)"
            )
            for phase in invalid_phases
        )

        return make_result(
            rule=rule,
            status="NON_COMPLIANT",
            reason=(
                "Certaines phases ne présentent pas "
                "toutes les informations obligatoires."
            ),
            evidence=evidence,
            recommendation=(
                "Indiquer pour chaque phase sa durée, "
                "son nombre de JEH et son prix HT."
            ),
        )

    return make_result(
        rule=rule,
        status="COMPLIANT",
        reason=(
            "Toutes les phases indiquent leur durée, "
            "leur nombre de JEH et leur prix HT."
        ),
    )

def get_phases(
    document: dict,
    section: str,
) -> list[dict]:
    return (
        document
        .get(section, {})
        .get("phases", [])
    )


def index_phases_by_number(
    phases: list[dict],
) -> dict[int, dict]:
    return {
        phase["number"]: phase
        for phase in phases
        if phase.get("number") is not None
    }

@register("RULE_015")
def check_phase_identity_consistency(
    document: dict,
    rule: dict,
) -> dict:

    methodology = get_phases(document, "methodology")
    planning = get_phases(document, "planning")
    budget = get_phases(document, "budget")

    if not methodology or not planning or not budget:
        return not_evaluated(
            rule,
            (
                "Les phases de méthodologie, planning ou budget "
                "n'ont pas toutes pu être extraites."
            ),
        )

    inconsistencies = []
    missing_data = []

    # ---------------------------------------------------------
    # 1. Méthodologie ↔ Planning : identité stricte
    # ---------------------------------------------------------

    methodology_sequence = [
        (phase.get("number"), phase.get("title"))
        for phase in methodology
    ]

    planning_sequence = [
        (phase.get("number"), phase.get("title"))
        for phase in planning
    ]

    if planning_sequence != methodology_sequence:
        inconsistencies.append(
            (
                "Méthodologie et planning ne contiennent pas "
                "exactement les mêmes phases dans le même ordre. "
                f"Méthodologie={methodology_sequence} ; "
                f"Planning={planning_sequence}"
            )
        )

    # ---------------------------------------------------------
    # 2. Méthodologie ↔ Budget
    #
    # Une phase gratuite (price_ht == 0) peut être absente
    # du budget.
    # ---------------------------------------------------------

    methodology_by_number = index_phases_by_number(
        methodology
    )

    budget_by_number = index_phases_by_number(
        budget
    )

    methodology_numbers = set(methodology_by_number.keys())
    budget_numbers = set(budget_by_number.keys())

    # Phases de méthodologie absentes du budget
    for number in sorted(
        methodology_numbers - budget_numbers
    ):
        phase = methodology_by_number[number]

        title = phase.get(
            "title",
            f"Phase {number}",
        )

        price_ht = phase.get("price_ht")

        # Phase explicitement gratuite :
        # son absence du budget est autorisée.
        if price_ht == 0:
            continue

        # Prix inconnu :
        # impossible de déterminer si l'absence est légitime.
        if price_ht is None:
            missing_data.append(
                (
                    f"Phase {number} « {title} » absente du budget "
                    "mais son prix HT n'a pas pu être déterminé"
                )
            )
            continue

        # Phase payante absente du budget
        inconsistencies.append(
            (
                f"Phase {number} « {title} » absente du budget "
                f"alors qu'elle est facturée {price_ht:.2f} € HT"
            )
        )

    # Phases présentes au budget mais absentes de la méthodologie
    for number in sorted(
        budget_numbers - methodology_numbers
    ):
        phase = budget_by_number[number]

        title = phase.get(
            "title",
            f"Phase {number}",
        )

        inconsistencies.append(
            (
                f"Phase {number} « {title} » présente dans le budget "
                "mais absente de la méthodologie"
            )
        )

    # ---------------------------------------------------------
    # 3. Pour les phases présentes dans les deux :
    # numéro + titre doivent être identiques
    # ---------------------------------------------------------

    common_numbers = methodology_numbers & budget_numbers

    for number in sorted(common_numbers):
        methodology_title = methodology_by_number[number].get(
            "title"
        )

        budget_title = budget_by_number[number].get(
            "title"
        )

        if methodology_title != budget_title:
            inconsistencies.append(
                (
                    f"Phase {number} : titre différent entre "
                    f"méthodologie « {methodology_title} » "
                    f"et budget « {budget_title} »"
                )
            )

    # ---------------------------------------------------------
    # 4. Vérification de l'ordre relatif des phases du budget
    # ---------------------------------------------------------

    methodology_order = [
        phase.get("number")
        for phase in methodology
    ]

    budget_order = [
        phase.get("number")
        for phase in budget
    ]

    expected_budget_order = [
        number
        for number in methodology_order
        if number in budget_numbers
    ]

    if budget_order != expected_budget_order:
        inconsistencies.append(
            (
                "L'ordre des phases du budget ne correspond pas "
                "à celui de la méthodologie. "
                f"Budget={budget_order} ; "
                f"ordre attendu={expected_budget_order}"
            )
        )

    # ---------------------------------------------------------
    # 5. Résultat
    # ---------------------------------------------------------

    if inconsistencies:
        return make_result(
            rule=rule,
            status="NON_COMPLIANT",
            reason=(
                "Les phases ne sont pas cohérentes entre "
                "la méthodologie, le planning et le budget."
            ),
            evidence="; ".join(inconsistencies),
            recommendation=(
                "Aligner les numéros, titres et l'ordre des phases "
                "entre les sections. Une phase explicitement "
                "gratuite peut être absente du budget."
            ),
        )

    if missing_data:
        return not_evaluated(
            rule,
            (
                "La cohérence des phases ne peut pas être "
                "entièrement vérifiée. "
                + "; ".join(missing_data)
            ),
        )

    return make_result(
        rule=rule,
        status="COMPLIANT",
        reason=(
            "Les phases sont cohérentes entre la méthodologie, "
            "le planning et le budget. Les éventuelles phases "
            "absentes du budget sont explicitement gratuites."
        ),
    )

@register("RULE_016")
def check_phase_duration_consistency(
    document: dict,
    rule: dict,
) -> dict:

    methodology = index_phases_by_number(
        get_phases(document, "methodology")
    )

    planning = index_phases_by_number(
        get_phases(document, "planning")
    )

    if not methodology or not planning:
        return not_evaluated(
            rule,
            "Les durées de méthodologie ou de planning "
            "n'ont pas pu être exploitées.",
        )

    common_numbers = (
        methodology.keys()
        & planning.keys()
    )

    if not common_numbers:
        return not_evaluated(
            rule,
            "Aucune phase commune n'a pu être identifiée.",
        )

    inconsistencies = []
    missing_values = []

    for number in sorted(common_numbers):
        methodology_duration = (
            methodology[number]
            .get("duration_weeks")
        )

        planning_duration = (
            planning[number]
            .get("duration_weeks")
        )

        if (
            methodology_duration is None
            or planning_duration is None
        ):
            missing_values.append(number)
            continue

        if methodology_duration != planning_duration:
            inconsistencies.append(
                (
                    number,
                    methodology_duration,
                    planning_duration,
                )
            )

    if inconsistencies:
        evidence = "; ".join(
            (
                f"Phase {number} : "
                f"méthodologie={method_duration} semaine(s), "
                f"planning={planning_duration} semaine(s)"
            )
            for (
                number,
                method_duration,
                planning_duration,
            ) in inconsistencies
        )

        return make_result(
            rule=rule,
            status="NON_COMPLIANT",
            reason=(
                "Certaines durées de phase diffèrent entre "
                "la méthodologie et le planning."
            ),
            evidence=evidence,
            recommendation=(
                "Aligner les durées des phases entre "
                "la méthodologie et le planning."
            ),
        )

    if missing_values:
        return not_evaluated(
            rule,
            (
                "Certaines durées nécessaires à la comparaison "
                f"sont absentes : phases {missing_values}."
            ),
        )

    return make_result(
        rule=rule,
        status="COMPLIANT",
        reason=(
            "Les durées des phases sont cohérentes entre "
            "la méthodologie et le planning."
        ),
    )

@register("RULE_017")
def check_total_duration_consistency(
    document: dict,
    rule: dict,
) -> dict:

    planning = document.get("planning", {})

    declared_duration = planning.get(
        "total_duration_weeks"
    )

    phases = planning.get("phases", [])

    if declared_duration is None or not phases:
        return not_evaluated(
            rule,
            "La durée totale ou le planning détaillé "
            "n'a pas pu être extrait.",
        )

    start_weeks = [
        phase.get("start_week")
        for phase in phases
        if phase.get("start_week") is not None
    ]

    end_weeks = [
        phase.get("end_week")
        for phase in phases
        if phase.get("end_week") is not None
    ]

    if not start_weeks or not end_weeks:
        return not_evaluated(
            rule,
            "Les positions temporelles des phases "
            "ne sont pas suffisamment renseignées.",
        )

    calculated_duration = (
        max(end_weeks)
        - min(start_weeks)
        + 1
    )

    if calculated_duration != declared_duration:
        return make_result(
            rule=rule,
            status="NON_COMPLIANT",
            reason=(
                "La durée totale annoncée ne correspond pas "
                "à la durée représentée dans le planning."
            ),
            evidence=(
                f"Durée annoncée : {declared_duration} semaine(s) ; "
                f"planning : {calculated_duration} semaine(s)."
            ),
            recommendation=(
                "Aligner la durée totale annoncée avec "
                "le planning détaillé."
            ),
        )

    return make_result(
        rule=rule,
        status="COMPLIANT",
        reason="La durée totale est cohérente avec le planning.",
        evidence=(
            f"Durée totale : {declared_duration} semaine(s)."
        ),
    )
@register("RULE_020")
def check_jeh_consistency(
    document: dict,
    rule: dict,
) -> dict:

    methodology = index_phases_by_number(
        get_phases(document, "methodology")
    )

    budget = index_phases_by_number(
        get_phases(document, "budget")
    )

    if not methodology or not budget:
        return not_evaluated(
            rule,
            (
                "Les phases de méthodologie ou de budget "
                "n'ont pas pu être exploitées."
            ),
        )

    inconsistencies = []
    missing_data = []

    methodology_numbers = set(methodology.keys())
    budget_numbers = set(budget.keys())

    # 1. Phases présentes dans la méthodologie mais absentes du budget
    for number in sorted(methodology_numbers - budget_numbers):
        phase = methodology[number]

        price_ht = phase.get("price_ht")
        title = phase.get("title", f"Phase {number}")

        # Une phase explicitement gratuite peut ne pas apparaître au budget.
        if price_ht == 0:
            continue

        # Si le prix n'a pas été extrait, on ne peut pas savoir
        # si l'absence du budget est légitime.
        if price_ht is None:
            missing_data.append(
                (
                    f"Phase {number} « {title} » absente du budget "
                    "et prix HT non disponible dans la méthodologie"
                )
            )
            continue

        # Une phase payante doit apparaître dans le budget.
        inconsistencies.append(
            (
                f"Phase {number} « {title} » absente du budget "
                f"alors que son prix est de {price_ht} € HT"
            )
        )

    # 2. Phases présentes dans le budget mais absentes de la méthodologie
    for number in sorted(budget_numbers - methodology_numbers):
        phase = budget[number]
        title = phase.get("title", f"Phase {number}")

        inconsistencies.append(
            (
                f"Phase {number} « {title} » présente dans le budget "
                "mais absente de la méthodologie"
            )
        )

    # 3. Comparaison des JEH pour les phases présentes dans les deux
    common_numbers = methodology_numbers & budget_numbers

    for number in sorted(common_numbers):
        methodology_jeh = methodology[number].get("jeh")
        budget_jeh = budget[number].get("jeh")

        title = methodology[number].get(
            "title",
            f"Phase {number}",
        )

        if methodology_jeh is None or budget_jeh is None:
            missing_data.append(
                (
                    f"Phase {number} « {title} » : "
                    "JEH manquants dans la méthodologie "
                    "ou le budget"
                )
            )
            continue

        if methodology_jeh != budget_jeh:
            inconsistencies.append(
                (
                    f"Phase {number} « {title} » : "
                    f"méthodologie={methodology_jeh} JEH, "
                    f"budget={budget_jeh} JEH"
                )
            )

    # 4. Une incohérence explicite prime sur les données manquantes
    if inconsistencies:
        return make_result(
            rule=rule,
            status="NON_COMPLIANT",
            reason=(
                "Les JEH ne sont pas cohérents entre "
                "la méthodologie et le budget."
            ),
            evidence="; ".join(inconsistencies),
            recommendation=(
                "Aligner les phases et les JEH du budget "
                "avec ceux annoncés dans la méthodologie. "
                "Une phase explicitement gratuite peut être "
                "absente du budget."
            ),
        )

    # 5. Pas d'incohérence prouvée, mais données insuffisantes
    if missing_data:
        return not_evaluated(
            rule,
            (
                "La cohérence des JEH ne peut pas être "
                "entièrement vérifiée. "
                + "; ".join(missing_data)
            ),
        )

    return make_result(
        rule=rule,
        status="COMPLIANT",
        reason=(
            "Les JEH sont cohérents entre la méthodologie "
            "et le budget. Les éventuelles phases absentes "
            "du budget sont explicitement gratuites."
        ),
    )
@register("RULE_021")
def check_phase_price_consistency(
    document: dict,
    rule: dict,
) -> dict:

    methodology = index_phases_by_number(
        get_phases(document, "methodology")
    )

    budget = index_phases_by_number(
        get_phases(document, "budget")
    )

    if not methodology or not budget:
        return not_evaluated(
            rule,
            (
                "Les phases de méthodologie ou de budget "
                "n'ont pas pu être exploitées."
            ),
        )

    inconsistencies = []
    missing_data = []

    methodology_numbers = set(methodology.keys())
    budget_numbers = set(budget.keys())

    # 1. Phases présentes dans la méthodologie
    # mais absentes du budget
    for number in sorted(
        methodology_numbers - budget_numbers
    ):
        phase = methodology[number]

        price_ht = phase.get("price_ht")
        title = phase.get(
            "title",
            f"Phase {number}",
        )

        # Une phase explicitement gratuite peut
        # légitimement être absente du budget.
        if price_ht == 0:
            continue

        # Sans prix, impossible de savoir si
        # l'absence du budget est légitime.
        if price_ht is None:
            missing_data.append(
                (
                    f"Phase {number} « {title} » absente du budget "
                    "et prix HT non disponible dans la méthodologie"
                )
            )
            continue

        # Une phase payante doit apparaître dans le budget.
        inconsistencies.append(
            (
                f"Phase {number} « {title} » absente du budget "
                f"alors que son prix est de {price_ht:.2f} € HT"
            )
        )

    # 2. Phases présentes dans le budget
    # mais absentes de la méthodologie
    for number in sorted(
        budget_numbers - methodology_numbers
    ):
        phase = budget[number]

        title = phase.get(
            "title",
            f"Phase {number}",
        )

        inconsistencies.append(
            (
                f"Phase {number} « {title} » présente dans le budget "
                "mais absente de la méthodologie"
            )
        )

    # 3. Comparaison des montants pour les phases communes
    common_numbers = methodology_numbers & budget_numbers

    for number in sorted(common_numbers):
        methodology_price = methodology[number].get(
            "price_ht"
        )

        budget_price = budget[number].get(
            "price_ht"
        )

        title = methodology[number].get(
            "title",
            f"Phase {number}",
        )

        if (
            methodology_price is None
            or budget_price is None
        ):
            missing_data.append(
                (
                    f"Phase {number} « {title} » : "
                    "prix HT manquant dans la méthodologie "
                    "ou le budget"
                )
            )
            continue

        if methodology_price != budget_price:
            inconsistencies.append(
                (
                    f"Phase {number} « {title} » : "
                    f"méthodologie={methodology_price:.2f} € HT, "
                    f"budget={budget_price:.2f} € HT"
                )
            )

    # 4. Une incohérence explicite prime
    if inconsistencies:
        return make_result(
            rule=rule,
            status="NON_COMPLIANT",
            reason=(
                "Les montants des phases ne sont pas cohérents "
                "entre la méthodologie et le budget."
            ),
            evidence="; ".join(inconsistencies),
            recommendation=(
                "Aligner les phases et leurs montants entre "
                "la méthodologie et le budget. "
                "Une phase explicitement gratuite peut être "
                "absente du budget."
            ),
        )

    # 5. Pas d'incohérence prouvée,
    # mais données insuffisantes
    if missing_data:
        return not_evaluated(
            rule,
            (
                "La cohérence des montants ne peut pas être "
                "entièrement vérifiée. "
                + "; ".join(missing_data)
            ),
        )

    return make_result(
        rule=rule,
        status="COMPLIANT",
        reason=(
            "Les montants des phases sont cohérents entre "
            "la méthodologie et le budget. Les éventuelles "
            "phases absentes du budget sont explicitement gratuites."
        ),
    )
@register("RULE_023")
def check_unit_jeh_price(
    document: dict,
    rule: dict,
) -> dict:

    phases = get_phases(document, "budget")

    if not phases:
        return not_evaluated(
            rule,
            "Aucune phase budgétaire n'a pu être extraite.",
        )

    parameters = rule.get("parameters", {})

    min_price = parameters.get("min_price_ht")
    max_price = parameters.get("max_price_ht")

    if min_price is None or max_price is None:
        return not_evaluated(
            rule,
            "Les seuils de prix par JEH ne sont pas configurés.",
        )

    invalid_phases = []
    missing_values = []

    for phase in phases:
        jeh = phase.get("jeh")
        price_ht = phase.get("price_ht")

        if jeh is None or price_ht is None:
            missing_values.append(phase.get("number"))
            continue

        if jeh <= 0:
            missing_values.append(phase.get("number"))
            continue

        unit_price = price_ht / jeh

        if not min_price <= unit_price <= max_price:
            invalid_phases.append(
                {
                    "number": phase.get("number"),
                    "title": phase.get("title"),
                    "unit_price": unit_price,
                }
            )

    if invalid_phases:
        evidence = "; ".join(
            (
                f"Phase {phase['number']} "
                f"« {phase['title']} » : "
                f"{phase['unit_price']:.2f} € HT/JEH"
            )
            for phase in invalid_phases
        )

        return make_result(
            rule=rule,
            status="NON_COMPLIANT",
            reason=(
                "Le prix unitaire de certains JEH est "
                "en dehors de la plage autorisée."
            ),
            evidence=evidence,
            recommendation=(
                f"Vérifier que le prix unitaire est compris "
                f"entre {min_price} et {max_price} € HT/JEH."
            ),
        )

    if missing_values:
        return not_evaluated(
            rule,
            (
                "Le prix par JEH ne peut pas être calculé "
                f"pour les phases {missing_values}."
            ),
        )

    return make_result(
        rule=rule,
        status="COMPLIANT",
        reason=(
            "Le prix unitaire par JEH respecte "
            "la plage autorisée pour toutes les phases."
        ),
    )


@register("REC_003")
def check_client_iterations(document,rule):
    phases = get_phases(document, "methodology")

    threshold = (
        rule.get("parameters", {})
        .get("review_threshold_per_week")
    )

    if threshold is None:
        return make_result(
            rule,
            "NOT_EVALUATED",
            "Le seuil d'allers-retours client n'est pas défini."
        )

    evaluated = []
    missing_duration = []

    for phase in phases:
        iterations = phase.get("client_iterations")

        if iterations is None:
            continue

        duration = phase.get("duration_weeks")

        if duration is None or duration <= 0:
            missing_duration.append(phase.get("title"))
            continue

        ratio = iterations / duration

        evaluated.append({
            "phase": phase.get("title"),
            "iterations": iterations,
            "duration": duration,
            "ratio": ratio,
        })

    exceeding = [
        item
        for item in evaluated
        if item["ratio"] > threshold
    ]

    if exceeding:
        details = "; ".join(
            f"{item['phase']}: "
            f"{item['iterations']} itérations / "
            f"{item['duration']} semaines = "
            f"{item['ratio']:.1f}/semaine"
            for item in exceeding
        )

        return make_result(
            rule,
            "SUGGESTED",
            (
                f"Le seuil de {threshold:g} aller-retour client "
                f"par semaine est dépassé. {details}."
            ),
            evidence=details,
            recommendation=(
                "Vérifier si ce volume d'allers-retours client "
                "est réellement nécessaire."
            ),
        )

    if missing_duration:
        return make_result(
            rule,
            "NOT_EVALUATED",
            (
                "Des itérations client sont renseignées mais la durée "
                "de certaines phases ne permet pas de calculer leur fréquence."
            ),
            evidence=", ".join(
                phase for phase in missing_duration if phase
            ) or None,
        )

    if evaluated:
        details = "; ".join(
            f"{item['phase']}: {item['ratio']:.1f}/semaine"
            for item in evaluated
        )

        return make_result(
            rule,
            "NOT_SUGGESTED",
            (
                f"Les fréquences explicites d'allers-retours client "
                f"ne dépassent pas le seuil de {threshold:g}/semaine."
            ),
            evidence=details,
        )

    return make_result(
        rule,
        "NOT_EVALUATED",
        "Aucun nombre d'allers-retours client n'est explicitement renseigné."
    )

@register("RULE_025")
def check_external_costs(document, rule):
    phases = get_phases(document, "methodology")

    resources = []

    for phase in phases:
        for resource in phase.get("external_resources") or []:
            resources.append({
                "phase": phase.get("title"),
                "resource": resource,
            })

    budget = document.get("budget") or {}
    external_costs = budget.get("external_costs") or []

    if not resources and not external_costs:
        return make_result(
            rule,
            "NOT_APPLICABLE",
            (
                "Aucune ressource externe n'est explicitement identifiée "
                "dans la méthodologie et aucun coût externe n'est budgété."
            ),
        )

    if not resources and external_costs:
        return make_result(
            rule,
            "NON_COMPLIANT",
            (
                "Le budget contient au moins un coût externe sans besoin "
                "externe identifiable dans la méthodologie."
            ),
            evidence=str(external_costs),
            recommendation=(
                "Relier chaque coût externe budgété à un besoin explicite "
                "dans la méthodologie."
            ),
        )

    if resources and not external_costs:
        return make_result(
            rule,
            "NOT_EVALUATED",
            (
                "Des ressources externes sont identifiées dans la méthodologie, "
                "mais aucun coût externe n'est budgété. Les données disponibles "
                "ne permettent pas de déterminer si ces ressources engendrent "
                "nécessairement un coût."
            ),
            evidence=str(resources),
        )

    return make_result(
        rule,
        "NOT_EVALUATED",
        (
            "Des ressources et des coûts externes sont présents, mais leur "
            "correspondance ne peut pas être vérifiée de manière déterministe."
        ),
        evidence=(
            f"Ressources : {resources}; "
            f"coûts : {external_costs}"
        ),
    )