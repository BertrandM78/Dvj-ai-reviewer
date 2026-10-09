import json
from pathlib import Path


RULES_PATH = Path("config/rules_v2.json")


def load_rules(path: Path = RULES_PATH) -> list[dict]:
    """Load and validate the V2 rule configuration."""

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    rules = data.get("rules")

    if not isinstance(rules, list):
        raise ValueError("rules_v2.json must contain a 'rules' list.")

    validate_rules(rules)

    return rules


def validate_rules(rules: list[dict]) -> None:
    required_fields = {
        "id",
        "title",
        "section",
        "type",
        "dimension",
        "engine",
        "severity",
        "applies_when",
        "description",
    }

    valid_types = {
        "OBLIGATION",
        "RECOMMENDATION",
    }

    valid_dimensions = {
        "FOND",
        "FORME",
    }

    valid_engines = {
        "LLM",
        "DETERMINISTIC",
        "RAW_TEXT_LLM"
    }

    valid_severities = {
        "CRITICAL",
        "MAJOR",
        "MINOR",
        "INFO",
    }

    seen_ids = set()

    for rule in rules:
        missing_fields = required_fields - rule.keys()

        if missing_fields:
            raise ValueError(
                f"{rule.get('id', 'UNKNOWN')}: "
                f"missing fields {sorted(missing_fields)}"
            )

        rule_id = rule["id"]

        if rule_id in seen_ids:
            raise ValueError(
                f"Duplicate rule id: {rule_id}"
            )

        seen_ids.add(rule_id)

        if rule["type"] not in valid_types:
            raise ValueError(
                f"{rule_id}: invalid type {rule['type']}"
            )

        if rule["dimension"] not in valid_dimensions:
            raise ValueError(
                f"{rule_id}: invalid dimension "
                f"{rule['dimension']}"
            )

        if rule["engine"] not in valid_engines:
            raise ValueError(
                f"{rule_id}: invalid engine "
                f"{rule['engine']}"
            )

        if rule["severity"] not in valid_severities:
            raise ValueError(
                f"{rule_id}: invalid severity "
                f"{rule['severity']}"
            )


def get_rules_by_engine(
    rules: list[dict],
    engine: str,
) -> list[dict]:
    return [
        rule
        for rule in rules
        if rule["engine"] == engine
    ]


def get_rules_by_type(
    rules: list[dict],
    rule_type: str,
) -> list[dict]:
    return [
        rule
        for rule in rules
        if rule["type"] == rule_type
    ]


if __name__ == "__main__":
    rules = load_rules()

    deterministic_rules = get_rules_by_engine(
        rules,
        "DETERMINISTIC",
    )

    llm_rules = get_rules_by_engine(
        rules,
        "LLM",
    )

    obligations = get_rules_by_type(
        rules,
        "OBLIGATION",
    )

    recommendations = get_rules_by_type(
        rules,
        "RECOMMENDATION",
    )

    print(f"Total: {len(rules)}")
    print(f"Deterministic: {len(deterministic_rules)}")
    print(f"LLM: {len(llm_rules)}")
    print(f"Obligations: {len(obligations)}")
    print(f"Recommendations: {len(recommendations)}")