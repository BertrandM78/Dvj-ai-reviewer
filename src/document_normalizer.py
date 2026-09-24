import json

from src.aws_client import get_aws_client
from pathlib import Path


REGION = "us-east-1"
MODEL_ID = "amazon.nova-pro-v1:0"


bedrock_client = get_aws_client(
    "bedrock-runtime",
    REGION,
)

NORMALIZER_PROMPT_PATH = Path(
    "prompts/normalizer_prompt.txt"
)


def load_normalizer_prompt() -> str:
    return NORMALIZER_PROMPT_PATH.read_text(
        encoding="utf-8"
    )


def normalize_document(proposal_text: str) -> dict:
    prompt_template = load_normalizer_prompt()

    prompt = prompt_template.replace(
        "{proposal_text}",
        proposal_text,
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
            "maxTokens": 4000,
        },
    )

    raw_output = response["output"]["message"]["content"][0]["text"]

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
        return json.loads(cleaned_output)

    except json.JSONDecodeError as exc:
        raise ValueError(
            "Nova returned invalid JSON.\n\n"
            f"Raw output:\n{raw_output}"
        ) from exc