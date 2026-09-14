import boto3
import json
from botocore.exceptions import ClientError

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

from retriever import proposal

prompt = f"""
You are a strict quality auditor reviewing a software development proposal.

Your task is to evaluate the proposal ONLY against the reference rules below.

IMPORTANT REVIEW PRINCIPLES:

1. A rule is COMPLIANT only if the proposal contains explicit evidence
   satisfying the requirement.

2. Do NOT infer missing information.

3. Do NOT assume that a requirement is satisfied because something
   vaguely related is mentioned.

4. If a required element is absent, ambiguous, implicit, or cannot be
   directly supported by the proposal text, classify the rule as
   NON_COMPLIANT.

5. Do NOT invent requirements that are not present in the reference rules.

For each rule:
- classify it as COMPLIANT or NON_COMPLIANT
- quote or identify the evidence from the proposal
- explain the reasoning
- if NON_COMPLIANT, provide a concrete recommendation
- Specify required elements; Evidence found ; Missing elements

Classification:
COMPLIANT / NON_COMPLIANT

EVIDENCE STANDARD:

- Compliance requires direct textual evidence for every required element of the rule.
- Each required element must be explicitly present in the proposal.
- Do not treat a later project phase as evidence that an earlier required phase exists.
- Words such as "implies", "suggests", "likely", "probably", "can be inferred", or similar reasoning must NEVER be used to justify COMPLIANT status.
- If a rule contains multiple requirements joined by "and", ALL requirements must be explicitly satisfied.
- If even one required element is missing, classify the rule as NON_COMPLIANT.

OUTPUT INSTRUCTIONS:

- Start directly with RULE 1.
- Do not include any introduction, preamble, conclusion, or summary.
- Output only the rule evaluations.

REFERENCE RULES:

{retrieved_context}

PROPOSAL TO REVIEW:

{proposal}
"""


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
print("\n" + "=" * 40)
print("Review of the proposal:")
print("=" * 40)
print(review)
