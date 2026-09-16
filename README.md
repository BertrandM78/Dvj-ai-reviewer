HOW RAG WORKS

RÈGLES DVJ
    ↓
   S3
    ↓
chunking
    ↓
embedding model
    ↓
[0.12, -0.84, 0.31, ...]
    ↓
S3 Vector Store


QUESTION
"Que manque-t-il dans cette propale ?"
    ↓
embedding de la question
    ↓
recherche des vecteurs similaires
    ↓
chunks pertinents
    ↓
LLM
    ↓
réponse + sources


## Current MVP

The current prototype:

1. stores proposal quality rules in an Amazon Bedrock Knowledge Base,
2. retrieves relevant rules using Bedrock managed retrieval,
3. injects retrieved rules into the LLM context,
4. reviews a fictitious proposal against those rules,
5. identifies compliant and non-compliant requirements.

Current evaluation:
- 5 fictitious quality rules
- 1 synthetic proposal
- 3 predefined violations


DEVELOPMENT BENCHMARK — FROZEN

Dataset:
4 synthetic proposals
5 rules
20 rule-level classifications

V1 — Llama 3 8B / initial prompt
Accuracy:  65.0%
Precision: 75.0%
Recall:    33.3%

V2 — Llama 3 8B / decision procedure
Accuracy:  70.0%
Precision: 80.0%
Recall:    44.4%

V3 — Nova Pro / same decision procedure
Accuracy:  90.0%
Precision: 88.9%
Recall:    88.9%

Remaining errors:
P3/R5 → conditional-rule / binary-label limitation
P4/R1 → semantic over-inference