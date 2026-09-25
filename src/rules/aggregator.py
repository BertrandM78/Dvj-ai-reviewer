from src.rules.loader import load_rules


ACTIVE_ENGINES = {
    "DETERMINISTIC",
    "LLM",
}


def aggregate_results(
    deterministic_results: list[dict],
    llm_results: list[dict],
    rules: list[dict] | None = None,
) -> list[dict]:
    """
    Merge V2 rule-engine results safely.

    Guarantees:
    - no duplicate result inside an engine
    - no collision between engines
    - every active rule has exactly one result
    - no unexpected rule is returned
    - output follows rules_v2.json order

    RAW_TEXT_LLM rules are intentionally excluded until that engine exists.
    """
    if rules is None:
        rules = load_rules()

    active_rules = [
        rule
        for rule in rules
        if rule["engine"] in ACTIVE_ENGINES
    ]

    expected_ids = {
        rule["id"]
        for rule in active_rules
    }

    deterministic_by_id = _index_results(
        deterministic_results,
        "DETERMINISTIC",
    )

    llm_by_id = _index_results(
        llm_results,
        "LLM",
    )

    deterministic_ids = set(deterministic_by_id)
    llm_ids = set(llm_by_id)

    collisions = deterministic_ids & llm_ids

    if collisions:
        raise ValueError(
            "Rule collision between DETERMINISTIC and LLM engines: "
            f"{sorted(collisions)}"
        )

    combined = {
        **deterministic_by_id,
        **llm_by_id,
    }

    actual_ids = set(combined)

    missing_ids = expected_ids - actual_ids
    unexpected_ids = actual_ids - expected_ids

    if missing_ids:
        raise ValueError(
            f"Missing rule results: {sorted(missing_ids)}"
        )

    if unexpected_ids:
        raise ValueError(
            f"Unexpected rule results: {sorted(unexpected_ids)}"
        )

    return [
        combined[rule["id"]]
        for rule in active_rules
    ]


def _index_results(
    results: list[dict],
    engine_name: str,
) -> dict[str, dict]:
    indexed = {}

    for result in results:
        rule_id = result.get("rule_id")

        if not rule_id:
            raise ValueError(
                f"{engine_name} result without rule_id."
            )

        if rule_id in indexed:
            raise ValueError(
                f"Duplicate {engine_name} result for {rule_id}."
            )

        indexed[rule_id] = result

    return indexed