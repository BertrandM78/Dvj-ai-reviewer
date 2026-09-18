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

