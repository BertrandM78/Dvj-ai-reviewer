from src.rules.aggregator import aggregate_results
from src.rules.deterministic import run_deterministic_rules
from src.rules.llm import run_llm_rules
from src.rules.loader import load_rules, get_rules_by_engine


def review_v2(
    normalized_document: dict,
) -> list[dict]:
    """
    Run the complete V2 review pipeline on a normalized document.

    Current active engines:
    - DETERMINISTIC
    - LLM

    RAW_TEXT_LLM rules are intentionally excluded until that engine exists.
    """
    rules = load_rules()

    deterministic_rules = get_rules_by_engine(
        rules,
        "DETERMINISTIC",
    )

    llm_rules = get_rules_by_engine(
        rules,
        "LLM",
    )

    deterministic_results = run_deterministic_rules(
        normalized_document,
        rules=deterministic_rules,
    )

    llm_results = run_llm_rules(
        normalized_document,
        rules=llm_rules,
    )

    return aggregate_results(
        deterministic_results=deterministic_results,
        llm_results=llm_results,
        rules=rules,
    )