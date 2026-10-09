def new_usage_collector() -> dict:
    return {
        "normalization": {
            "calls": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "bedrock_latency_ms": 0,
        },
        "review": {
            "calls": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "bedrock_latency_ms": 0,
        },
        "retrieval": {
            "calls": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "bedrock_latency_ms": 0,
        },
    }


def record_converse_usage(
    collector: dict | None,
    stage: str,
    response: dict,
) -> None:
    if collector is None:
        return

    stage_usage = collector.setdefault(
        stage,
        {
            "calls": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "bedrock_latency_ms": 0,
        },
    )

    usage = response.get(
        "usage",
        {},
    )

    metrics = response.get(
        "metrics",
        {},
    )

    input_tokens = int(
        usage.get("inputTokens", 0)
        or 0
    )

    output_tokens = int(
        usage.get("outputTokens", 0)
        or 0
    )

    total_tokens = int(
        usage.get(
            "totalTokens",
            input_tokens + output_tokens,
        )
        or 0
    )

    latency_ms = int(
        metrics.get("latencyMs", 0)
        or 0
    )

    stage_usage["calls"] += 1

    stage_usage["input_tokens"] += (
        input_tokens
    )

    stage_usage["output_tokens"] += (
        output_tokens
    )

    stage_usage["total_tokens"] += (
        total_tokens
    )

    stage_usage["bedrock_latency_ms"] += (
        latency_ms
    )


def summarize_usage(
    collector: dict,
) -> dict:
    summary = {
        "calls": sum(
            stage.get("calls", 0)
            for stage in collector.values()
        ),
        "input_tokens": sum(
            stage.get("input_tokens", 0)
            for stage in collector.values()
        ),
        "output_tokens": sum(
            stage.get("output_tokens", 0)
            for stage in collector.values()
        ),
        "total_tokens": sum(
            stage.get("total_tokens", 0)
            for stage in collector.values()
        ),
        "bedrock_latency_ms": sum(
            stage.get(
                "bedrock_latency_ms",
                0,
            )
            for stage in collector.values()
        ),
        "by_stage": {
            stage_name: dict(stage_usage)
            for stage_name, stage_usage in collector.items()
        },
    }

    return summary