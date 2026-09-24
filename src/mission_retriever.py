import json
from pathlib import Path

REGION = "us-east-1"
KB_ID = "DJ33HADJNL"
MODEL_ID = "amazon.nova-pro-v1:0"

HISTORICAL_PROMPT_PATH = Path(
    "prompts/historical_summary_prompt.txt"
)

from src.aws_client import get_aws_client


client = get_aws_client(
    "bedrock-agent-runtime",
    REGION,
)

bedrock_runtime = get_aws_client(
    "bedrock-runtime",
    REGION,
)

def load_historical_prompt() -> str:
    return HISTORICAL_PROMPT_PATH.read_text(
        encoding="utf-8"
    )

def retrieve(query: str, number_of_results: int = 5) -> list:
    response = client.retrieve(
        knowledgeBaseId=KB_ID,
        retrievalQuery={
            "text": query
        },
        retrievalConfiguration={
            "managedSearchConfiguration": {
                "numberOfResults": number_of_results
            }
        },
    )

    return response.get("retrievalResults", [])


def retrieve_references(
    sector: str,
    mission_type: str,
    number_of_results: int = 5,
) -> dict:
    sector_results = retrieve(
        f"Entreprise du secteur : {sector}",
        number_of_results,
    )

    mission_results = retrieve(
        f"Type de prestation : {mission_type}",
        number_of_results,
    )

    return {
        "sector": sector_results,
        "mission_type": mission_results,
    }

def generate_reference_summary(
    sector: str,
    mission_type: str,
    references: dict,
) -> str:

    sector_results = [
        result.get("content", {}).get("text", "")
        for result in references["sector"]
    ]

    mission_results = [
        result.get("content", {}).get("text", "")
        for result in references["mission_type"]
    ]

    prompt_template = load_historical_prompt()

    prompt = (
        prompt_template
        .replace("{sector}", sector)
        .replace("{mission_type}", mission_type)
        .replace(
            "{sector_results}",
            json.dumps(
                sector_results,
                ensure_ascii=False,
                indent=2,
            ),
        )
        .replace(
            "{mission_results}",
            json.dumps(
                mission_results,
                ensure_ascii=False,
                indent=2,
            ),
        )
    )

    response = bedrock_runtime.converse(
        modelId=MODEL_ID,
        messages=[
            {
                "role": "user",
                "content": [{"text": prompt}],
            }
        ],
        inferenceConfig={
            "temperature": 0.0,
            "maxTokens": 300,
        },
    )

    return response[
        "output"
    ]["message"]["content"][0]["text"].strip()


if __name__ == "__main__":
    references = retrieve_references(
        sector="Santé",
        mission_type="Application web",
    )

    summary = generate_reference_summary(
        sector="Santé",
        mission_type="Application web",
        references=references,
    )

    print(summary)