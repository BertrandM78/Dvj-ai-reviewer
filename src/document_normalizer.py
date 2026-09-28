import json
from pathlib import Path

from src.aws_client import get_aws_client


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


def normalize_document(proposal_text: str) -> dict:
    prompt = build_normalizer_prompt(
        proposal_text
    )

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

    raw_output = (
        response["output"]["message"]["content"][0]["text"]
    )

    # Defensive cleanup in case the model still returns a Markdown fence.
    cleaned_output = raw_output.strip()

    if cleaned_output.startswith("```json"):
        cleaned_output = cleaned_output[7:]

    if cleaned_output.startswith("```"):
        cleaned_output = cleaned_output[3:]

    if cleaned_output.endswith("```"):
        cleaned_output = cleaned_output[:-3]

    cleaned_output = cleaned_output.strip()

    try:
        normalized_document = json.loads(cleaned_output)
        return normalized_document

    except json.JSONDecodeError as exc:
        raise ValueError(
            "Nova returned invalid JSON.\n\n"
            f"Raw output:\n{raw_output}"
        ) from exc
