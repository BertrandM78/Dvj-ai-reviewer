import boto3
from botocore.exceptions import ClientError

REGION = "us-east-1"
KNOWLEDGE_BASE_ID = "DJ33HADJNL"

client = boto3.client(
    "bedrock-agent-runtime",
    region_name=REGION
)

query = "What rule applies to project deliverables?"

response = client.retrieve(
    knowledgeBaseId=KNOWLEDGE_BASE_ID,
    retrievalQuery={
        "text": query
    },
    retrievalConfiguration={
        "managedSearchConfiguration": {
            "numberOfResults": 3
        }
    }
)

results = response["retrievalResults"]

for result in results:
    print("SCORE:", result["score"])
    print("TEXT:", result["content"]["text"])
    print("-" * 50)