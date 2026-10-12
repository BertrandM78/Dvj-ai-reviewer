import json
import statistics
from collections import Counter
from pathlib import Path
import tomllib

import boto3


REGION = "us-east-1"
LOG_PREFIX = "logs/requests/"

STAGES = (
    "normalization",
    "review",
    "retrieval",
)


# ============================================================
# AWS / SECRETS
# ============================================================

def load_local_secrets() -> dict:
    secrets_path = Path(
        ".streamlit/secrets.toml"
    )

    with secrets_path.open("rb") as file:
        return tomllib.load(file)


def create_s3_client(secrets: dict):
    return boto3.client(
        "s3",
        region_name=REGION,
        aws_access_key_id=(
            secrets["AWS_ACCESS_KEY_ID"]
        ),
        aws_secret_access_key=(
            secrets["AWS_SECRET_ACCESS_KEY"]
        ),
    )


# ============================================================
# HELPERS
# ============================================================

def safe_mean(values: list[float]) -> float:
    if not values:
        return 0.0

    return statistics.mean(values)


def percentile(
    values: list[float],
    percentile_value: float,
) -> float:
    if not values:
        return 0.0

    values = sorted(values)

    index = (
        len(values) - 1
    ) * percentile_value

    lower = int(index)

    upper = min(
        lower + 1,
        len(values) - 1,
    )

    weight = index - lower

    return (
        values[lower] * (1 - weight)
        + values[upper] * weight
    )


def get_total_tokens(log: dict) -> int:
    """
    Support current log schema and remain defensive
    if the schema evolves.
    """

    usage_total = log.get(
        "usage_total",
        {},
    )

    if usage_total:
        return int(
            usage_total.get(
                "total_tokens",
                0,
            )
            or 0
        )

    # Compatibility with an older flat usage schema.
    usage = log.get(
        "usage",
        {},
    )

    return int(
        usage.get(
            "total_tokens",
            0,
        )
        or 0
    )


def get_model_cost(log: dict) -> float:
    cost = log.get(
        "cost",
        {},
    )

    if isinstance(cost, dict):
        return float(
            cost.get(
                "estimated_model_cost_usd",
                0,
            )
            or 0
        )

    return float(
        log.get(
            "estimated_cost_usd",
            0,
        )
        or 0
    )


# ============================================================
# LOAD LOGS
# ============================================================

def load_logs(
    s3,
    bucket: str,
) -> list[dict]:

    logs = []

    paginator = s3.get_paginator(
        "list_objects_v2"
    )

    for page in paginator.paginate(
        Bucket=bucket,
        Prefix=LOG_PREFIX,
    ):
        for item in page.get(
            "Contents",
            [],
        ):
            key = item["Key"]

            if not key.endswith(".json"):
                continue

            response = s3.get_object(
                Bucket=bucket,
                Key=key,
            )

            payload = json.loads(
                response["Body"]
                .read()
                .decode("utf-8")
            )

            payload["_s3_key"] = key

            logs.append(payload)

    return sorted(
        logs,
        key=lambda log: log.get(
            "timestamp",
            "",
        ),
    )


# ============================================================
# ANALYSIS
# ============================================================

def analyze(logs: list[dict]) -> None:

    if not logs:
        print(
            "No request logs found."
        )
        return

    successful = [
        log
        for log in logs
        if log.get("success") is True
    ]

    failed = [
        log
        for log in logs
        if log.get("success") is not True
    ]

    success_rate = (
        len(successful)
        / len(logs)
        * 100
    )

    total_times = [
        float(
            log
            .get("timings", {})
            .get("total_s", 0)
            or 0
        )
        for log in successful
    ]

    tokens = [
        get_total_tokens(log)
        for log in successful
    ]

    costs = [
        get_model_cost(log)
        for log in successful
    ]

    # ========================================================
    # HEADER
    # ========================================================

    print()
    print(
        "DVJ Proposal Reviewer — Logs"
    )
    print("=" * 40)

    # ========================================================
    # REQUESTS
    # ========================================================

    print()
    print("Requests")

    print(
        f"  Total               "
        f"{len(logs)}"
    )

    print(
        f"  Successful          "
        f"{len(successful)}"
    )

    print(
        f"  Failed              "
        f"{len(failed)}"
    )

    print(
        f"  Success rate        "
        f"{success_rate:.1f} %"
    )

    # ========================================================
    # LATENCY
    # ========================================================

    if total_times:

        print()
        print("Latency")

        print(
            f"  Average             "
            f"{safe_mean(total_times):.2f} s"
        )

        print(
            f"  Median              "
            f"{statistics.median(total_times):.2f} s"
        )

        print(
            f"  P95                 "
            f"{percentile(total_times, 0.95):.2f} s"
        )

        print(
            f"  Min                 "
            f"{min(total_times):.2f} s"
        )

        print(
            f"  Max                 "
            f"{max(total_times):.2f} s"
        )

    # ========================================================
    # NOVA
    # ========================================================

    print()
    print("Nova Pro")

    if tokens:

        print(
            f"  Avg tokens          "
            f"{safe_mean(tokens):,.0f}"
        )

        print(
            f"  Total tokens        "
            f"{sum(tokens):,}"
        )

    print(
        f"  Avg model cost      "
        f"${safe_mean(costs):.4f}"
    )

    print(
        f"  Total model cost    "
        f"${sum(costs):.4f}"
    )

    if successful and not any(
        token_count > 0
        for token_count in tokens
    ):
        print()
        print(
            "  ⚠ WARNING: all successful requests "
            "contain 0 tokens."
        )
        print(
            "    The usage collector or log schema "
            "is probably not wired correctly."
        )

    # ========================================================
    # BY STAGE
    # ========================================================

    print()
    print("By stage")

    for stage in STAGES:

        stage_times = [
            float(
                log
                .get("timings", {})
                .get(
                    f"{stage}_s",
                    0,
                )
                or 0
            )
            for log in successful
        ]

        stage_usage = [
            log
            .get("usage_by_stage", {})
            .get(stage, {})
            for log in successful
        ]

        stage_tokens = [
            int(
                usage.get(
                    "total_tokens",
                    0,
                )
                or 0
            )
            for usage in stage_usage
        ]

        stage_calls = [
            int(
                usage.get(
                    "calls",
                    0,
                )
                or 0
            )
            for usage in stage_usage
        ]

        bedrock_latencies = [
            int(
                usage.get(
                    "bedrock_latency_ms",
                    0,
                )
                or 0
            )
            for usage in stage_usage
        ]

        print()
        print(
            f"  {stage.capitalize()}"
        )

        print(
            f"    Avg time          "
            f"{safe_mean(stage_times):.2f} s"
        )

        print(
            f"    Avg Nova calls    "
            f"{safe_mean(stage_calls):.1f}"
        )

        print(
            f"    Avg tokens        "
            f"{safe_mean(stage_tokens):,.0f}"
        )

        if any(
            latency > 0
            for latency in bedrock_latencies
        ):
            print(
                f"    Avg Bedrock       "
                f"{safe_mean(bedrock_latencies):.0f} ms"
            )

        # Optional support if stopReason is later logged.
        stop_counter = Counter()

        for usage in stage_usage:

            stop_reasons = usage.get(
                "stop_reasons",
                {},
            )

            if isinstance(
                stop_reasons,
                dict,
            ):
                stop_counter.update(
                    stop_reasons
                )

        if stop_counter:
            formatted = ", ".join(
                f"{reason}={count}"
                for reason, count
                in stop_counter.items()
            )

            print(
                f"    Stop reasons      "
                f"{formatted}"
            )

    # ========================================================
    # BUSINESS RESULTS
    # ========================================================

    if successful:

        print()
        print("Review results")

        result_fields = (
            "total_controls",
            "compliant",
            "non_compliant",
            "not_evaluated",
            "not_applicable",
            "suggestions",
            "commercial_references",
            "signed_mission_references",
        )

        for field in result_fields:

            values = [
                int(
                    log
                    .get("results", {})
                    .get(field, 0)
                    or 0
                )
                for log in successful
            ]

            if any(values):

                label = (
                    field
                    .replace("_", " ")
                    .capitalize()
                )

                print(
                    f"  Avg {label:<24}"
                    f"{safe_mean(values):.1f}"
                )

    # ========================================================
    # FAILURE SUMMARY
    # ========================================================

    if failed:

        print()
        print("Failure summary")

        stage_counter = Counter(
            log.get(
                "error_stage",
                "unknown",
            )
            for log in failed
        )

        error_counter = Counter(
            log.get(
                "error_type",
                "unknown",
            )
            for log in failed
        )

        print(
            "  By stage            "
            + ", ".join(
                f"{key}={value}"
                for key, value
                in stage_counter.items()
            )
        )

        print(
            "  By error            "
            + ", ".join(
                f"{key}={value}"
                for key, value
                in error_counter.items()
            )
        )

        # ====================================================
        # FAILURE DETAILS
        # ====================================================

        print()
        print("Failures")

        for log in failed:

            request_id = log.get(
                "request_id",
                "unknown",
            )

            timestamp = log.get(
                "timestamp",
                "unknown",
            )

            stage = log.get(
                "error_stage",
                "unknown",
            )

            error_type = log.get(
                "error_type",
                "unknown",
            )

            timings = log.get(
                "timings",
                {},
            )

            total_time = float(
                timings.get(
                    "total_s",
                    0,
                )
                or 0
            )

            print()

            print(
                f"  {request_id[:8]} "
                f"· {timestamp}"
            )

            print(
                f"    Stage             "
                f"{stage}"
            )

            print(
                f"    Error             "
                f"{error_type}"
            )

            print(
                f"    Total time        "
                f"{total_time:.2f} s"
            )

            # Show how far execution got.
            for timing_stage in (
                "parsing",
                "normalization",
                "retrieval",
                "review",
            ):

                duration = float(
                    timings.get(
                        f"{timing_stage}_s",
                        0,
                    )
                    or 0
                )

                if duration > 0:

                    print(
                        f"    "
                        f"{timing_stage.capitalize():<17}"
                        f"{duration:.2f} s"
                    )

            # Usage accumulated before failure.
            usage_by_stage = log.get(
                "usage_by_stage",
                {},
            )

            accumulated_tokens = sum(
                int(
                    stage_usage.get(
                        "total_tokens",
                        0,
                    )
                    or 0
                )
                for stage_usage
                in usage_by_stage.values()
                if isinstance(
                    stage_usage,
                    dict,
                )
            )

            if accumulated_tokens:

                print(
                    f"    Tokens before fail "
                    f"{accumulated_tokens:,}"
                )

    print()


# ============================================================
# MAIN
# ============================================================

def main():
    secrets = load_local_secrets()

    bucket = secrets[
        "LOG_BUCKET"
    ]

    s3 = create_s3_client(
        secrets
    )

    logs = load_logs(
        s3,
        bucket,
    )

    analyze(logs)


if __name__ == "__main__":
    main()