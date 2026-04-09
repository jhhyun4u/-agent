"""
모델별 토큰 가격 상수 + 비용 계산 유틸리티.

Anthropic 공식 가격 기준 (2025-05 기준, per 1M tokens).
"""

# 모델별 가격 (USD per 1M tokens)
MODEL_PRICING: dict[str, dict[str, float]] = {
    "claude-sonnet-4-5-20250929": {
        "input": 3.00,
        "output": 15.00,
        "cache_read": 0.30,
        "cache_create": 3.75,
    },
    "claude-haiku-4-5-20251001": {
        "input": 0.80,
        "output": 4.00,
        "cache_read": 0.08,
        "cache_create": 1.00,
    },
    "claude-opus-4-6": {
        "input": 15.00,
        "output": 75.00,
        "cache_read": 1.50,
        "cache_create": 18.75,
    },
}

# 기본 가격 (알 수 없는 모델용)
_DEFAULT_PRICING = MODEL_PRICING["claude-sonnet-4-5-20250929"]


def calculate_cost(
    input_tokens: int,
    output_tokens: int,
    cache_read: int = 0,
    cache_create: int = 0,
    model: str = "",
) -> float:
    """토큰 수 기반 USD 비용 계산."""
    pricing = MODEL_PRICING.get(model, _DEFAULT_PRICING)
    regular_input = max(0, input_tokens - cache_read - cache_create)
    return round(
        regular_input * pricing["input"] / 1_000_000
        + output_tokens * pricing["output"] / 1_000_000
        + cache_read * pricing["cache_read"] / 1_000_000
        + cache_create * pricing["cache_create"] / 1_000_000,
        6,
    )


def summarize_usage(records: list[dict]) -> dict:
    """여러 API 호출 기록을 단일 요약으로 합산."""
    total_input = 0
    total_output = 0
    total_cache_read = 0
    total_cache_create = 0
    model = ""

    for r in records:
        total_input += r.get("input_tokens", 0)
        total_output += r.get("output_tokens", 0)
        total_cache_read += r.get("cache_read_input_tokens", 0)
        total_cache_create += r.get("cache_creation_input_tokens", 0)
        model = r.get("model", model)

    cost = calculate_cost(total_input, total_output, total_cache_read, total_cache_create, model)

    return {
        "input_tokens": total_input,
        "output_tokens": total_output,
        "cache_read_tokens": total_cache_read,
        "cache_create_tokens": total_cache_create,
        "total_tokens": total_input + total_output,
        "cost_usd": cost,
        "model": model,
        "num_calls": len(records),
    }


class TokenCostTracker:
    """제안서 워크플로우 중 누적된 토큰 비용을 추적하는 클래스."""

    @staticmethod
    def format_cost(cost_usd: float) -> str:
        """USD 비용을 포맷팅된 문자열로 변환.

        Examples:
            0.00234 → "$0.00"
            4.2567 → "$4.26"
            150.0 → "$150.00"
        """
        return f"${cost_usd:.2f}"

    @staticmethod
    def format_elapsed_time(elapsed_seconds: int) -> str:
        """초 단위 시간을 포맷팅된 문자열로 변환.

        Examples:
            65 → "1m 5s"
            3661 → "1h 1m 1s"
            7200 → "2h 0m"
        """
        hours = elapsed_seconds // 3600
        minutes = (elapsed_seconds % 3600) // 60
        seconds = elapsed_seconds % 60

        if hours > 0:
            return f"{hours}h {minutes}m"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"

    @staticmethod
    def aggregate_costs(cost_records: list[dict]) -> dict:
        """여러 토큰 기록을 집계하여 총 비용 계산.

        Args:
            cost_records: [
                {"input_tokens": 100, "output_tokens": 50, "model": "claude-sonnet-4-5-20250929"},
                ...
            ]

        Returns:
            {
                "total_tokens": 150,
                "total_cost_usd": 0.001234,
                "total_cost_formatted": "$0.00",
                "model": "claude-sonnet-4-5-20250929"
            }
        """
        return summarize_usage(cost_records)
