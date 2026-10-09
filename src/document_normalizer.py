import json
from pathlib import Path
import re 
from src.aws_client import get_aws_client
from src.llm_usage import (
    record_converse_usage,
)

REGION = "us-east-1"
MODEL_ID = "amazon.nova-pro-v1:0"

NORMALIZER_PROMPT_PATH = Path(
    "prompts/normalizer_prompt.txt"
)

NORMALIZED_SCHEMA_PATH = Path(
    "config/normalized_document_schema_v2.json"
)

bedrock_client = get_aws_client(
    "bedrock-runtime",
    REGION,
)


def load_normalizer_prompt() -> str:
    return NORMALIZER_PROMPT_PATH.read_text(
        encoding="utf-8"
    )


def load_normalized_schema() -> dict:
    with NORMALIZED_SCHEMA_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def build_normalizer_prompt(proposal_text: str) -> str:
    prompt_template = load_normalizer_prompt()
    schema = load_normalized_schema()

    schema_text = json.dumps(
        schema,
        ensure_ascii=False,
        indent=2,
    )

    return (
        prompt_template
        .replace(
            "{normalized_document_schema}",
            schema_text,
        )
        .replace(
            "{proposal_text}",
            proposal_text,
        )
    )

def call_normalizer(
    proposal_text: str,
    usage_collector: dict | None = None,
) -> dict:
    prompt = build_normalizer_prompt(proposal_text)

    response = bedrock_client.converse(
        modelId=MODEL_ID,
        messages=[
            {
                "role": "user",
                "content": [{"text": prompt}],
            }
        ],
        inferenceConfig={
            "temperature": 0.0,
            "maxTokens": 6000,
        },
    )
    record_converse_usage(
        usage_collector,
        "normalization",
        response,
    )

    raw_output = (
        response["output"]["message"]["content"][0]["text"]
    )

    cleaned_output = raw_output.strip()

    if cleaned_output.startswith("```json"):
        cleaned_output = cleaned_output[7:]

    if cleaned_output.startswith("```"):
        cleaned_output = cleaned_output[3:]

    if cleaned_output.endswith("```"):
        cleaned_output = cleaned_output[:-3]

    cleaned_output = cleaned_output.strip()

    try:
        return json.loads(cleaned_output)

    except json.JSONDecodeError as exc:
        raise ValueError(
            "Nova returned invalid JSON.\n\n"
            f"Raw output:\n{raw_output}"
        ) from exc


def extract_pages_from_text(
    proposal_text: str,
    page_numbers: set[int],
) -> str:
    page_pattern = re.compile(
        r"(?ms)^--- PAGE (\d+) ---\n"
        r"(.*?)(?=^--- PAGE \d+ ---|\Z)"
    )

    selected_pages = []

    for match in page_pattern.finditer(proposal_text):
        page_number = int(match.group(1))

        if page_number in page_numbers:
            selected_pages.append(
                f"--- PAGE {page_number} ---\n"
                f"{match.group(2).strip()}"
            )

    return "\n\n".join(selected_pages)


def get_budget_page_numbers(
    normalized_document: dict,
) -> set[int]:
    slides = (
        normalized_document
        .get("document", {})
        .get("slides", [])
    )

    return {
        int(slide["page"])
        for slide in slides
        if slide.get("detected_section") == "BUDGET"
        and slide.get("page") is not None
    }
def enrich_tender_fees(
    normalized_document: dict,
) -> None:
    """
    Populate tender_fees_ht when an explicitly identified
    tender-related external cost has already been extracted.

    Handles minor text-extraction corruption by accepting
    tender platform costs even when the word "offre" is malformed.
    """
    budget = (
        normalized_document
        .get("document", {})
        .get("budget", {})
    )

    if budget.get("tender_fees_ht") is not None:
        return

    tender_costs = []

    for cost in budget.get("external_costs", []):
        name = str(cost.get("name") or "").casefold()
        amount = cost.get("amount_ht")

        is_tender_cost = (
            "appel" in name
            and (
                "offre" in name
                or "plateforme" in name
            )
        )

        if is_tender_cost and amount is not None:
            tender_costs.append(amount)

    if tender_costs:
        budget["tender_fees_ht"] = sum(tender_costs)

def normalize_document(
    proposal_text: str,
    usage_collector: dict | None = None,
) -> dict:
    # Pass 1:
    # Normalize the complete proposal.
    normalized_document = call_normalizer(
        proposal_text,
        usage_collector=usage_collector,
    )

    # Identify pages that the global pass classified as BUDGET.
    budget_page_numbers = get_budget_page_numbers(
        normalized_document
    )

    if not budget_page_numbers:
        enrich_tender_fees(normalized_document)
        return normalized_document

    # Isolate the raw budget pages to avoid cross-section
    # contamination from methodology/planning values.
    budget_text = extract_pages_from_text(
        proposal_text,
        budget_page_numbers,
    )

    if not budget_text.strip():
        enrich_tender_fees(normalized_document)
        return normalized_document

    # Pass 2:
    # Normalize only the budget pages.
    budget_document = call_normalizer(
        budget_text,
        usage_collector=usage_collector,
    )

    isolated_budget = (
        budget_document
        .get("document", {})
        .get("budget")
    )

    if isolated_budget is not None:
        normalized_document["document"]["budget"] = (
            isolated_budget
        )

    enrich_tender_fees(normalized_document)

    return normalized_document