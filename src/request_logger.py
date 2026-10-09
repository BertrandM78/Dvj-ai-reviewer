import json
import uuid
from datetime import datetime, timezone

import streamlit as st

from src.aws_client import get_aws_client


REGION = "us-east-1"
LOG_PREFIX = "logs/requests"
NOVA_PRO_INPUT_PRICE_PER_M = 0.80
NOVA_PRO_OUTPUT_PRICE_PER_M = 3.20

s3_client = get_aws_client("s3", REGION)


def create_request_id() -> str:
    return str(uuid.uuid4())


def estimate_nova_cost(input_tokens: int, output_tokens: int) -> float:
    return (
        input_tokens / 1_000_000 * NOVA_PRO_INPUT_PRICE_PER_M
        + output_tokens / 1_000_000 * NOVA_PRO_OUTPUT_PRICE_PER_M
    )


def log_request(
    *,
    request_id: str,
    filename: str,
    file_size_bytes: int,
    timings: dict,
    usage: dict,
    result_summary: dict,
    success: bool,
    error_stage: str | None = None,
    error_type: str | None = None,
    app_version: str = "v1.0",
) -> bool:
    now = datetime.now(timezone.utc)
    input_tokens = int(usage.get("input_tokens", 0) or 0)
    output_tokens = int(usage.get("output_tokens", 0) or 0)
    total_tokens = int(
        usage.get("total_tokens", input_tokens + output_tokens) or 0
    )
    payload = {
        "request_id": request_id,
        "timestamp": now.isoformat(),
        "filename": filename,
        "file_size_bytes": file_size_bytes,
        "timings": timings,
        "usage": {
            **usage,
            "total_tokens": total_tokens,
        },
        "estimated_model_cost_usd": round(
            estimate_nova_cost(input_tokens, output_tokens), 6
        ),
        "cost_scope": (
            "Nova Pro inference only; excludes Knowledge Base, "
            "vector store, and S3 costs."
        ),
        "results": result_summary,
        "success": success,
        "error_stage": error_stage,
        "error_type": error_type,
        "app_version": app_version,
    }
    key = f"{LOG_PREFIX}/{now:%Y-%m-%d}/{request_id}.json"

    try:
        bucket = st.secrets["LOG_BUCKET"]
        s3_client.put_object(
            Bucket=bucket,
            Key=key,
            Body=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            ContentType="application/json",
        )
    except Exception:
        return False

    return True
