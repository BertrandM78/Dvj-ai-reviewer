import json

REGION = "us-east-1"
KB_ID = "DJ33HADJNL"
MODEL_ID = "amazon.nova-pro-v1:0"

from src.aws_client import get_aws_client


client = get_aws_client(
    "bedrock-agent-runtime",
    REGION,
)

bedrock_runtime = get_aws_client(
    "bedrock-runtime",
    REGION,
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

    prompt = f"""
You are analyzing historical commercial data from DeVinci Junior.

NEW PROPOSAL
Sector: {sector}
Mission type: {mission_type}

RETRIEVED BY SECTOR
{json.dumps(sector_results, ensure_ascii=False, indent=2)}

RETRIEVED BY MISSION TYPE
{json.dumps(mission_results, ensure_ascii=False, indent=2)}

Your task is to produce a factual and cautious French paragraph that can
be directly included in a proposal review report.

The goal is not to make DeVinci Junior look experienced.
The goal is to accurately summarize what the retrieved historical data
supports.

Rules:
- Filter out irrelevant retrieval results.
- Never invent information.
- Only use information explicitly present in the retrieved data.
- Distinguish carefully between a lead, a sent proposal, a signed study,
  and a completed mission.
- Never say that DeVinci Junior "réalisé" or "mené" a mission unless the
  retrieved data explicitly proves it.
- Sector similarity and mission-type similarity are independent signals.
- Do not claim that a company belongs to the requested sector unless the
  retrieved data provides sufficient evidence.
- If no relevant sector reference exists, say so.
- If no relevant mission-type reference exists, say so.
- Do not force a reference combining both sector and mission type.
- Prefer signed studies over unsuccessful commercial leads when available.
- Do not expose personal information such as names, emails or phone numbers.
- Be concise: maximum 100 words.
- Write only the final French paragraph. No JSON, no title, no markdown.
- Never infer absence from retrieval.
- If no relevant reference is retrieved, say:
  "Parmi les références récupérées, aucune ne permet de confirmer..."
  Never say that DeVinci Junior has never done such a mission.

- Respect commercial statuses literally:
  * "Étude signée" means only that the study was signed.
  * "Envoyé" means only that a proposal was sent.
  * "Fermé", "client injoignable", "projet annulé", etc. must never
    be presented as completed missions.
  * Never transform "signed" into "completed", "conducted" or "delivered".

- Relevant unsuccessful leads may still be mentioned as
  "opportunités commerciales" when they provide useful sector experience,
  but clearly state that they do not prove a completed mission.

- When sector and mission-type references exist separately, summarize
  both and explicitly state whether the retrieved data proves a reference
  combining both dimensions.

- Base conclusions only on the retrieved results, not on the entire
  historical activity of DeVinci Junior.
"""

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

    return response["output"]["message"]["content"][0]["text"].strip()

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