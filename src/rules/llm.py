import json
from pathlib import Path

from src.aws_client import get_aws_client
from src.rules.loader import load_rules
from src.llm_usage import (
    record_converse_usage,
)


REGION = "us-east-1"
MODEL_ID = "amazon.nova-pro-v1:0"

PROMPT_PATH = Path(
    "prompts/reviewer_prompt_v2.txt"
)

bedrock_client = get_aws_client(
    "bedrock-runtime",
    REGION,
)


def load_llm_prompt() -> str:
    return PROMPT_PATH.read_text(
        encoding="utf-8"
    )


def get_llm_rules() -> list[dict]:
    rules = load_rules()

    return [
        rule
        for rule in rules
        if rule.get("engine") == "LLM"
    ]


def clean_json_output(raw_output: str) -> str:
    cleaned = raw_output.strip()

    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]

    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]

    return cleaned.strip()


def run_llm_rules(
    normalized_document: dict,
    rules: list[dict],
    usage_collector: dict | None = None,
) -> list[dict]:

    if rules is None:
        rules = get_llm_rules()

    if not rules:
        return []

    prompt_template = load_llm_prompt()

    prompt = prompt_template.replace(
        "{rules}",
        json.dumps(
            rules,
            ensure_ascii=False,
            indent=2,
        ),
    )

    prompt = prompt.replace(
        "{normalized_document}",
        json.dumps(
            normalized_document,
            ensure_ascii=False,
            indent=2,
        ),
    )

    response = bedrock_client.converse(
        modelId=MODEL_ID,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "text": prompt,
                    }
                ],
            }
        ],
        inferenceConfig={
            "temperature": 0.0,
            "maxTokens": 5000,
        },
    )
    record_converse_usage(
        usage_collector,
        "review",
        response,
    )

    raw_output = (
        response["output"]
        ["message"]
        ["content"][0]
        ["text"]
    )

    cleaned_output = clean_json_output(
        raw_output
    )

    try:
        results = json.loads(cleaned_output)

    except json.JSONDecodeError as exc:
        raise ValueError(
            "Nova returned invalid JSON.\n\n"
            f"Raw output:\n{raw_output}"
        ) from exc

    validate_llm_results(
        results=results,
        rules=rules,
    )

    return results


def validate_llm_results(
    results: list[dict],
    rules: list[dict],
) -> None:

    if not isinstance(results, list):
        raise ValueError(
            "LLM rule engine must return a JSON array."
        )

    expected_rules = {
        rule["id"]: rule
        for rule in rules
    }

    expected_ids = set(expected_rules.keys())

    result_ids = []

    for result in results:
        if not isinstance(result, dict):
            raise ValueError(
                "Each LLM result must be a JSON object."
            )

        rule_id = result.get("rule_id")

        if not rule_id:
            raise ValueError(
                "An LLM result is missing rule_id."
            )

        result_ids.append(rule_id)

    # Duplicate detection
    if len(result_ids) != len(set(result_ids)):
        raise ValueError(
            "LLM returned duplicate rule IDs."
        )

    actual_ids = set(result_ids)

    missing_ids = expected_ids - actual_ids
    unexpected_ids = actual_ids - expected_ids

    if missing_ids:
        raise ValueError(
            "LLM did not evaluate all requested rules. "
            f"Missing: {sorted(missing_ids)}"
        )

    if unexpected_ids:
        raise ValueError(
            "LLM evaluated rules that were not requested. "
            f"Unexpected: {sorted(unexpected_ids)}"
        )

    # Status validation
    obligation_statuses = {
        "COMPLIANT",
        "NON_COMPLIANT",
        "NOT_APPLICABLE",
        "NOT_EVALUATED",
    }

    recommendation_statuses = {
        "SUGGESTED",
        "NOT_SUGGESTED",
    }

    for result in results:
        rule_id = result["rule_id"]
        status = result.get("status")

        rule = expected_rules[rule_id]
        rule_type = rule["type"]

        if rule_type == "OBLIGATION":
            allowed_statuses = obligation_statuses

        elif rule_type == "RECOMMENDATION":
            allowed_statuses = recommendation_statuses

        else:
            raise ValueError(
                f"Unknown rule type for {rule_id}: "
                f"{rule_type}"
            )

        if status not in allowed_statuses:
            raise ValueError(
                f"Invalid status for {rule_id}: "
                f"{status}. "
                f"Allowed: {sorted(allowed_statuses)}"
            )