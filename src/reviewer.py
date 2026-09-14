import boto3
import json
from botocore.exceptions import ClientError
from pathlib import Path
from retriever import proposal

REGION = "us-east-1"
KNOWLEDGE_BASE_ID = "DJ33HADJNL"

kb_client = boto3.client(
    "bedrock-agent-runtime",
    region_name=REGION
)


def retrieve_rules(query):
    response = kb_client.retrieve(
        knowledgeBaseId=KNOWLEDGE_BASE_ID,
        retrievalQuery={
            "text": query
        },
        retrievalConfiguration={
            "managedSearchConfiguration": {
                "numberOfResults": 5
            }
        }
    )

    return response["retrievalResults"]

retrieval_query = """
Retrieve the quality rules that should be used to review
a software development proposal.
"""

results = retrieve_rules(retrieval_query)

#for result in results:
#    print(result["content"]["text"])

#---------------------------------------------------------------------------------------------------------

retrieved_context = "\n\n".join(
    result["content"]["text"]
    for result in results
)


PROMPT_PATH = Path("prompts/reviewer_prompt.txt")

prompt_template = PROMPT_PATH.read_text(encoding="utf-8")

prompt = (
    prompt_template
    .replace("{{REFERENCE_RULES}}", retrieved_context)
    .replace("{{PROPOSAL}}", proposal)
)


bedrock_client = boto3.client("bedrock-runtime", region_name=REGION)


def generate_review(prompt_text):
    response = bedrock_client.converse(
        modelId="meta.llama3-8b-instruct-v1:0",
        messages=[
            {
                "role": "user",
                "content": [{"text": prompt_text}]
            }
        ],
        inferenceConfig={
            "temperature": 0.0,
            "maxTokens": 1000
        }
    )

    return response["output"]["message"]["content"][0]["text"]




review = generate_review(prompt)
review_data = json.loads(review)
print("\n" + "=" * 40)
print("Review of the proposal:")
print("=" * 40)
#print(review)
violations = [
    result
    for result in review_data["results"]
    if result["status"] == "NON_COMPLIANT"
]

print(f"\n{len(violations)} violations detected\n")

for violation in violations:
    print(f"{violation['rule_id']} — {violation['rule_name']}")
    print(f"Reason: {violation['reasoning']}")
    print(f"Recommendation: {violation['recommendation']}")
    print()

OUTPUT_PATH = Path("data/results/proposal_001_review.json")

OUTPUT_PATH.parent.mkdir(
    parents=True,
    exist_ok=True
)

with OUTPUT_PATH.open("w", encoding="utf-8") as f:
    json.dump(
        review_data,
        f,
        indent=2,
        ensure_ascii=False
    )