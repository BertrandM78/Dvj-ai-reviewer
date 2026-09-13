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
