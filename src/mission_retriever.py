import json
import re
import unicodedata
from typing import Literal

from src.aws_client import get_aws_client
from pathlib import Path
from src.historical_parser import (
    parse_historical_record,
)

REGION = "us-east-1"
KB_ID = "DJ33HADJNL"
MODEL_ID = "amazon.nova-pro-v1:0"

COMMERCIAL_PROPOSALS_FILE = "commercial_proposals.csv"
SIGNED_MISSIONS_FILE = "signed_missions.csv"

HISTORICAL_RERANK_PROMPT_PATH = Path(
    "prompts/historical_rerank_prompt.txt"
)


def load_rerank_prompt() -> str:
    return HISTORICAL_RERANK_PROMPT_PATH.read_text(
        encoding="utf-8"
    )

CorpusType = Literal[
    "COMMERCIAL_PROPOSAL",
    "SIGNED_MISSION",
]


bedrock_agent_runtime = get_aws_client(
    "bedrock-agent-runtime",
    REGION,
)

bedrock_runtime = get_aws_client(
    "bedrock-runtime",
    REGION,
)


# ---------------------------------------------------------------------------
# Query
# ---------------------------------------------------------------------------

def build_retrieval_query(
    sector: str,
    mission_type: str,
) -> str:
    """
    Build the semantic query used to retrieve similar historical missions.
    """

    parts = [
        "Recherche de missions similaires.",
    ]

    if sector:
        parts.append(
            f"Secteur ou contexte client : {sector}."
        )

    if mission_type:
        parts.append(
            f"Type de mission ou prestation : {mission_type}."
        )

    parts.append(
        "Prioriser la similarité du besoin client, "
        "de la prestation réalisée, des livrables "
        "et du contexte métier."
    )

    return " ".join(parts)


# ---------------------------------------------------------------------------
# Corpus helpers
# ---------------------------------------------------------------------------

def get_document_title(
    corpus_type: CorpusType,
) -> str:
    """
    Map an internal corpus type to the corresponding KB document.
    """

    if corpus_type == "COMMERCIAL_PROPOSAL":
        return COMMERCIAL_PROPOSALS_FILE

    if corpus_type == "SIGNED_MISSION":
        return SIGNED_MISSIONS_FILE

    raise ValueError(
        f"Unsupported corpus type: {corpus_type}"
    )


def get_source_uri(
    result: dict,
) -> str:
    """
    Extract the source URI from a Bedrock retrieval result.
    """

    location = result.get(
        "location",
        {},
    )

    s3_location = location.get(
        "s3Location",
        {},
    )

    uri = s3_location.get("uri")

    if uri:
        return uri

    metadata = result.get(
        "metadata",
        {},
    )

    source_uri = metadata.get(
        "_source_uri"
    )

    if isinstance(source_uri, str):
        return source_uri

    return ""


def detect_corpus(
    result: dict,
) -> CorpusType | None:
    """
    Identify the corpus from the source document.
    """

    metadata = result.get(
        "metadata",
        {},
    )

    document_title = str(
        metadata.get(
            "_document_title",
            "",
        )
    ).lower()

    source_uri = get_source_uri(
        result
    ).lower()

    if (
        document_title
        == COMMERCIAL_PROPOSALS_FILE.lower()
        or COMMERCIAL_PROPOSALS_FILE.lower()
        in source_uri
    ):
        return "COMMERCIAL_PROPOSAL"

    if (
        document_title
        == SIGNED_MISSIONS_FILE.lower()
        or SIGNED_MISSIONS_FILE.lower()
        in source_uri
    ):
        return "SIGNED_MISSION"

    return None


# ---------------------------------------------------------------------------
# Bedrock Knowledge Base retrieval
# ---------------------------------------------------------------------------

def retrieve_raw(
    query: str,
    corpus_type: CorpusType,
    number_of_results: int = 8,
) -> list[dict]:
    """
    Retrieve semantic candidates from exactly one historical corpus.

    The corpus is filtered directly inside Bedrock using _document_title.
    """

    document_title = get_document_title(
        corpus_type
    )

    response = bedrock_agent_runtime.retrieve(
        knowledgeBaseId=KB_ID,
        retrievalQuery={
            "text": query,
        },
        retrievalConfiguration={
            "managedSearchConfiguration": {
                "numberOfResults": number_of_results,
                "filter": {
                    "equals": {
                        "key": "_document_title",
                        "value": document_title,
                    }
                },
            }
        },
    )

    return response.get(
        "retrievalResults",
        [],
    )


# ---------------------------------------------------------------------------
# Candidate normalization
# ---------------------------------------------------------------------------

def normalize_candidates(
    results: list[dict],
    corpus_type: CorpusType,
) -> list[dict]:
    """
    Convert Bedrock retrieval results into a stable internal structure.

    Historical facts remain exactly sourced from the KB.
    """

    prefix = (
        "PROP"
        if corpus_type == "COMMERCIAL_PROPOSAL"
        else "MISSION"
    )

    normalized = []

    for index, result in enumerate(
        results,
        start=1,
    ):
        detected_corpus = detect_corpus(
            result
        )

        if detected_corpus != corpus_type:
            raise RuntimeError(
                "Unexpected corpus returned by Bedrock: "
                f"expected={corpus_type}, "
                f"received={detected_corpus}, "
                f"source={get_source_uri(result)}"
            )

        text = (
            result
            .get("content", {})
            .get("text", "")
            .strip()
        )

        if not text:
            continue

        record = parse_historical_record(
            text=text,
            corpus_type=corpus_type,
        )

        if not record:
            continue

        normalized.append(
            {
                "candidate_id": (
                    f"{prefix}_{index:02d}"
                ),
                "corpus_type": corpus_type,
                "record": record,
                "source_uri": get_source_uri(
                    result
                ),
                "retrieval_score": (
                    result.get("score")
                ),
            }
        )

    return normalized


# ---------------------------------------------------------------------------
# Corpus-specific retrieval
# ---------------------------------------------------------------------------

def retrieve_candidates(
    query: str,
    corpus_type: CorpusType,
    candidate_count: int = 8,
) -> list[dict]:
    """
    Retrieve candidates from one historical corpus.
    """

    raw_results = retrieve_raw(
        query=query,
        corpus_type=corpus_type,
        number_of_results=candidate_count,
    )

    return normalize_candidates(
        raw_results,
        corpus_type,
    )


# ---------------------------------------------------------------------------
# Nova reranking
# ---------------------------------------------------------------------------

def rerank_candidates(
    query: str,
    candidates: list[dict],
    top_k: int = 3,
) -> list[dict]:
    """
    Ask Nova Pro to select the most relevant historical candidates.

    Nova only selects candidate IDs and explains similarity.
    It is not allowed to generate historical facts.
    """

    if not candidates:
        return []

    candidate_payload = [
        {
            "candidate_id": candidate[
                "candidate_id"
            ],
            "record": candidate[
                "record"
            ],
        }
        for candidate in candidates
    ]

    prompt_template = load_rerank_prompt()

    requested_top_k = min(
        top_k,
        len(candidates),
    )

    prompt = (
        prompt_template
        .replace("{query}", query)
        .replace(
            "{candidates}",
            json.dumps(
                candidate_payload,
                ensure_ascii=False,
                indent=2,
            ),
        )
        .replace(
            "{top_k}",
            str(requested_top_k),
        )
    )

    response = bedrock_runtime.converse(
        modelId=MODEL_ID,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "text": prompt,
                    }
                ],
            }
        ],
        inferenceConfig={
            "temperature": 0.0,
            "maxTokens": 700,
        },
    )

    raw_output = (
        response["output"]
        ["message"]
        ["content"][0]
        ["text"]
        .strip()
    )

    # Defensive cleanup if Nova wraps JSON in markdown fences.
    if raw_output.startswith("```"):
        raw_output = raw_output.strip("`").strip()

        if raw_output.startswith("json"):
            raw_output = (
                raw_output[4:]
                .strip()
            )

    parsed = json.loads(
        raw_output
    )

    ranked_results = parsed.get(
        "results",
        [],
    )

    candidates_by_id = {
        candidate["candidate_id"]: candidate
        for candidate in candidates
    }

    final_results = []

    for ranked in ranked_results:
        candidate_id = ranked.get(
            "candidate_id"
        )

        relevance_score = ranked.get(
            "relevance_score",
            0,
        )

        if relevance_score < 60:
            continue

        candidate = candidates_by_id.get(
            candidate_id
        )

        if not candidate:
            continue    
        
        final_results.append(
            {
                **candidate,
                "relevance_score": relevance_score,
                "similarity_reason": ranked.get(
                    "similarity_reason",
                    "",
                ),
            }
        )

        if len(final_results) >= requested_top_k:
            break

    return final_results

# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def normalize_match_text(
    value: str | None,
) -> str:
    if not value:
        return ""

    value = unicodedata.normalize(
        "NFKD",
        value,
    )

    value = "".join(
        char
        for char in value
        if not unicodedata.combining(char)
    )

    value = value.casefold()

    value = re.sub(
        r"[^a-z0-9]+",
        " ",
        value,
    )

    return " ".join(
        value.split()
    )


def same_historical_case(
    proposal: dict,
    mission: dict,
) -> bool:
    proposal_record = proposal["record"]
    mission_record = mission["record"]

    proposal_company = normalize_match_text(
        proposal_record.get("company")
    )

    mission_company = normalize_match_text(
        mission_record.get("company")
    )

    if (
        not proposal_company
        or not mission_company
        or proposal_company != mission_company
    ):
        return False

    proposal_title = normalize_match_text(
        proposal_record.get("title")
    )

    mission_title = normalize_match_text(
        mission_record.get("title")
    )

    if not proposal_title or not mission_title:
        return False

    return (
        proposal_title in mission_title
        or mission_title in proposal_title
    )


def deduplicate_history(
    commercial_proposals: list[dict],
    signed_missions: list[dict],
) -> tuple[list[dict], list[dict]]:
    """
    If one historical case appears in both corpora,
    keep the signed mission and remove the proposal.
    """

    commercial_proposals = [
        proposal
        for proposal in commercial_proposals
        if not any(
            same_historical_case(
                proposal,
                mission,
            )
            for mission in signed_missions
        )
    ]

    return (
        commercial_proposals,
        signed_missions,
    )

def retrieve_similar_history(
    sector: str,
    mission_type: str,
    candidate_count: int = 8,
    top_k: int = 3,
) -> dict:
    """
    Retrieve and rerank historical references.

    Returns two independent corpora:
    - commercial proposals
    - signed missions
    """

    query = build_retrieval_query(
        sector=sector,
        mission_type=mission_type,
    )

    commercial_candidates = (
        retrieve_candidates(
            query=query,
            corpus_type=(
                "COMMERCIAL_PROPOSAL"
            ),
            candidate_count=candidate_count,
        )
    )

    signed_mission_candidates = (
        retrieve_candidates(
            query=query,
            corpus_type="SIGNED_MISSION",
            candidate_count=candidate_count,
        )
    )

    commercial_proposals = (
        rerank_candidates(
            query=query,
            candidates=(
                commercial_candidates
            ),
            top_k=top_k,
        )
    )

    signed_missions = (
        rerank_candidates(
            query=query,
            candidates=(
                signed_mission_candidates
            ),
            top_k=top_k,
        )
    )
    commercial_proposals, signed_missions = (
        deduplicate_history(
            commercial_proposals,
            signed_missions,
        )
    )

    return {
        "query": query,
        "commercial_proposals": (
            commercial_proposals
        ),
        "signed_missions": (
            signed_missions
        ),
    }

def build_query_from_normalized_document(
    normalized_document: dict,
) -> tuple[str, str]:
    """
    Extract the minimum information required for historical retrieval.
    """

    document = normalized_document.get(
        "document",
        {},
    )

    client_context = document.get(
        "client_context",
        {},
    )

    solution = document.get(
        "solution",
        {},
    )

    methodology = document.get(
        "methodology",
        {},
    )

    sector = (
        client_context.get("sector")
        or client_context.get("activity")
        or client_context.get("company_activity")
        or ""
    )

    mission_type = (
        solution.get("summary")
        or solution.get("description")
        or ""
    )

    if not mission_type:
        phases = methodology.get(
            "phases",
            [],
        )

        phase_titles = [
            phase.get("title")
            for phase in phases
            if phase.get("title")
        ]

        mission_type = " / ".join(
            phase_titles[:4]
        )

    return (
        str(sector).strip(),
        str(mission_type).strip(),
    )
def retrieve_similar_history_from_document(
    normalized_document: dict,
    candidate_count: int = 8,
    top_k: int = 3,
) -> dict:
    sector, mission_type = (
        build_query_from_normalized_document(
            normalized_document
        )
    )

    if not sector and not mission_type:
        return {
            "query": "",
            "commercial_proposals": [],
            "signed_missions": [],
        }

    return retrieve_similar_history(
        sector=sector,
        mission_type=mission_type,
        candidate_count=candidate_count,
        top_k=top_k,
    )

# ---------------------------------------------------------------------------
# Manual test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    results = retrieve_similar_history(
        sector="Industrie",
        mission_type=(
            "Bilan carbone et trajectoire "
            "de réduction"
        ),
    )

    print(
        json.dumps(
            results,
            ensure_ascii=False,
            indent=2,
        )
    )