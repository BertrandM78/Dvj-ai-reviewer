import boto3
from botocore.exceptions import ClientError

client = boto3.client(
    "bedrock-runtime",
    region_name="us-east-1"
)

model_id = "amazon.nova-micro-v1:0"

proposal = """
DeVinci Junior proposes to develop a web application
for Client X.

The project will last 8 weeks.

Phase 1: Requirements analysis
Phase 2: Development
Phase 3: Delivery
"""

proposal = """
DeVinci Junior proposes to develop a web application
for Client X.

The project will last 8 weeks.

Phase 1: Requirements analysis
Phase 2: Development
Phase 3: Delivery
"""

prompt = f"""
You are reviewing a consulting proposal.

Analyze the following proposal.

Identify:
1. Potential weaknesses
2. Missing information
3. Project risks
4. Recommendations

PROPOSAL:
{proposal}
"""


messages = [
    {
        "role": "user",
        "content": [
            {
                "text": prompt
            }
        ],
    }
]

try:
    response = client.converse(
        modelId=model_id,
        messages=messages,
        inferenceConfig={
            "maxTokens": 200,
            "temperature": 0.2,
        },
    )

    print(response["output"]["message"]["content"][0]["text"])

except ClientError as e:
    print(e)