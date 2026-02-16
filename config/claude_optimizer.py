"""
Claude 모델 전략 및 토큰/비용 최적화.

v3.0: 다단계 모델 티어링 + 한국어 토큰 최적화

설계: Part VII - Claude 모델 전략 및 토큰/비용 최적화
"""

from enum import Enum
from typing import Literal
from langchain_anthropic import ChatAnthropic


class ModelTier(str, Enum):
    """Claude 모델 티어"""
    OPUS = "claude-opus-4-5-20250929"      # 최고 성능, 가장 비쌈
    SONNET = "claude-sonnet-4-5-20250929"  # 최적 균형
    HAIKU = "claude-haiku-4-5-20251001"    # 초고속, 저비용


class ModelConfig:
    """모델별 가격 및 특성"""

    PRICES = {
        ModelTier.OPUS: {
            "input": 5.00,              # $/MTok
            "output": 25.00,
            "cache_write": 6.25,
            "cache_read": 0.50,
        },
        ModelTier.SONNET: {
            "input": 3.00,
            "output": 15.00,
            "cache_write": 3.75,
            "cache_read": 0.30,
        },
        ModelTier.HAIKU: {
            "input": 0.80,
            "output": 4.00,
            "cache_write": 1.00,
            "cache_read": 0.08,
        },
    }

    CONTEXT_WINDOWS = {
        ModelTier.OPUS: 200_000,
        ModelTier.SONNET: 200_000,
        ModelTier.HAIKU: 200_000,
    }

    @staticmethod
    def get_safe_limit(model: ModelTier) -> int:
        """모델의 안전 토큰 한도 (출력 여유 80% 사용)"""
        limit = ModelConfig.CONTEXT_WINDOWS.get(model, 200_000)
        return int(limit * 0.80)


# ═══════════════════════════════════════════════════════════════════════════
# 노드별 모델 배정 전략
# ═══════════════════════════════════════════════════════════════════════════

NODE_MODEL_TIER = {
    # Supervisor (판단 정확성 중요)
    "supervisor_plan": ModelTier.SONNET,
    "supervisor_route": None,  # LLM 미사용 (규칙 기반)

    # RFP 분석 에이전트
    "extract_document": None,
    "clean_text": None,
    "structural_analysis": ModelTier.SONNET,
    "implicit_analysis": ModelTier.SONNET,
    "client_language": ModelTier.HAIKU,
    "qualification_check": ModelTier.HAIKU,

    # 전략 수립 에이전트
    "analyze_competition": ModelTier.SONNET,
    "allocate_resources": ModelTier.HAIKU,
    "develop_strategy": ModelTier.SONNET,
    "assign_personnel": ModelTier.HAIKU,

    # 섹션 생성 에이전트 (기본값, 섹션별 오버라이드 가능)
    "plan_phases": ModelTier.HAIKU,
    "generate_section": ModelTier.SONNET,

    # 품질 관리 에이전트
    "critique_sections": ModelTier.SONNET,
    "check_consistency": ModelTier.HAIKU,
    "revise_sections": ModelTier.HAIKU,

    # 문서 출력 에이전트
    "gen_exec_summary": ModelTier.SONNET,
    "final_edit": ModelTier.SONNET,
    "apply_template": None,
    "export_document": None,
}


# 섹션별 모델 오버라이드
SECTION_MODEL_TIER = {
    # Sonnet: 전략적 사고, 창의적 작문 필요
    "sec_01_understanding": ModelTier.SONNET,
    "sec_02_strategy": ModelTier.SONNET,
    "sec_03_methodology": ModelTier.SONNET,
    "sec_06_budget": ModelTier.SONNET,
    "sec_07_outcomes": ModelTier.SONNET,

    # Haiku: 정형 구조, 데이터 나열 중심 (Few-shot으로 품질 보완)
    "sec_04_organization": ModelTier.HAIKU,
    "sec_05_schedule": ModelTier.HAIKU,
    "sec_08_risk": ModelTier.HAIKU,
    "sec_09_references": ModelTier.HAIKU,
}


def get_node_model(node_name: str) -> ModelTier | None:
    """노드명으로 사용할 모델 반환"""
    return NODE_MODEL_TIER.get(node_name)


def get_section_model(section_id: str) -> ModelTier:
    """섹션 ID로 사용할 모델 반환 (기본값: Sonnet)"""
    return SECTION_MODEL_TIER.get(section_id, ModelTier.SONNET)


def create_llm(model_tier: ModelTier, temperature: float = 0, **kwargs) -> ChatAnthropic:
    """모델을 생성합니다"""
    return ChatAnthropic(model=model_tier.value, temperature=temperature, **kwargs)


# ═══════════════════════════════════════════════════════════════════════════
# 한국어 토큰 관리 (Claude 특화)
# ═══════════════════════════════════════════════════════════════════════════

class TokenBudget:
    """Claude 모델용 토큰 예산 관리"""

    # Claude 토크나이저의 한국어 처리 특성:
    # - 한글 1글자 ≈ 1.2토큰 (평균)
    # - 영문/숫자 ≈ 0.25토큰/글자
    # - 공백/기호 ≈ 0.5토큰

    @staticmethod
    def estimate_tokens_korean(text: str) -> int:
        """한국어 텍스트의 Claude 토큰 수 추정"""
        korean_chars = sum(1 for c in text if '\uac00' <= c <= '\ud7a3')
        ascii_chars = sum(1 for c in text if c.isascii() and c.isalnum())
        other_chars = len(text) - korean_chars - ascii_chars

        return int(korean_chars * 1.2 + ascii_chars * 0.25 + other_chars * 0.5)

    @staticmethod
    def truncate_for_context(text: str, max_tokens: int) -> str:
        """최대 토큰 수에 맞게 텍스트 자르기"""
        # Claude 한국어 역변환: 1토큰 ≈ 0.83글자
        max_chars = int(max_tokens * 0.83)
        if len(text) <= max_chars:
            return text
        return text[:max_chars] + "\n\n... (분량 초과로 이하 생략)"

    @staticmethod
    def budget_for_node(node_name: str) -> dict:
        """노드별 토큰 예산 가이드"""
        BUDGETS = {
            "structural_analysis": {"input": 50_000, "output": 8_000},
            "implicit_analysis": {"input": 30_000, "output": 5_000},
            "develop_strategy": {"input": 40_000, "output": 10_000},
            "generate_section": {"input": 60_000, "output": 15_000},
            "critique_sections": {"input": 80_000, "output": 10_000},
            "gen_exec_summary": {"input": 50_000, "output": 8_000},
        }
        return BUDGETS.get(node_name, {"input": 40_000, "output": 8_000})

    @staticmethod
    def max_tokens_for_section(target_pages: float) -> int:
        """섹션 목표 분량에 맞는 max_tokens 동적 계산.
        
        한국어 ~2,160토큰/페이지 × 1.2 마진.
        고정 max_tokens는 짧은 섹션에서 장황한 출력을,
        긴 섹션에서 잘림을 유발하므로, 동적으로 설정.
        """
        TOKENS_PER_PAGE_KO = 2_160
        return int(target_pages * TOKENS_PER_PAGE_KO * 1.2)


# ═══════════════════════════════════════════════════════════════════════════
# Effort 파라미터 설정
# ═══════════════════════════════════════════════════════════════════════════

EFFORT_CONFIG = {
    # 간단한 작업 (low)
    "client_language": "low",
    "qualification_check": "low",
    "allocate_resources": "low",
    "check_consistency": "low",
    "plan_phases": "low",
    "assign_personnel": "low",

    # 복잡한 작업 (high)
    "develop_strategy": "high",
    "critique_sections": "high",
    "gen_exec_summary": "high",

    # 기본값 (medium)
}


def get_effort(node_name: str) -> Literal["low", "medium", "high"]:
    """노드의 Effort 파라미터"""
    return EFFORT_CONFIG.get(node_name, "medium")


# ═══════════════════════════════════════════════════════════════════════════
# Extended Thinking 설정
# ═══════════════════════════════════════════════════════════════════════════

THINKING_CONFIG = {
    # (enable, budget_tokens)
    "implicit_analysis": (True, 4_000),   # 숨은 의도 5~7개 추론에 충분
    "develop_strategy": (True, 8_000),    # SWOT 기반 전략 도출에 충분
    "critique_sections": (True, 5_000),   # 6대 축 평가에 충분
    "gen_exec_summary": (False, 0),       # 정보 취합 중심 → 불필요
}


def should_use_thinking(node_name: str) -> bool:
    """노드에서 Extended Thinking 사용 여부"""
    config = THINKING_CONFIG.get(node_name, (False, 0))
    return config[0]


def get_thinking_budget(node_name: str) -> int:
    """노드의 Extended Thinking 예산"""
    config = THINKING_CONFIG.get(node_name, (False, 0))
    return config[1]


# ═══════════════════════════════════════════════════════════════════════════
# 토큰 사용량 모니터링
# ═══════════════════════════════════════════════════════════════════════════

class TokenUsageTracker:
    """노드별 토큰 사용량 추적 및 비용 계산"""

    def __init__(self):
        self.records = []

    def record(
        self,
        node_name: str,
        model_tier: ModelTier,
        input_tokens: int,
        output_tokens: int,
        cache_creation_tokens: int = 0,
        cache_read_tokens: int = 0,
    ):
        """토큰 사용 기록"""
        cost = self._calculate_cost(
            model_tier, input_tokens, output_tokens,
            cache_creation_tokens, cache_read_tokens
        )

        self.records.append({
            "node": node_name,
            "model": model_tier.value,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cache_creation": cache_creation_tokens,
            "cache_read": cache_read_tokens,
            "cost_usd": cost,
        })

    def _calculate_cost(
        self,
        model_tier: ModelTier,
        input_tokens: int,
        output_tokens: int,
        cache_creation: int = 0,
        cache_read: int = 0,
    ) -> float:
        """사용 비용 계산"""
        prices = ModelConfig.PRICES[model_tier]

        # 입력 비용 = (전체 입력 토큰 - 캐시 관련) × 기본가 + 캐시 생성 × 높은가 + 캐시 읽기 × 낮은가
        input_cost = (
            (input_tokens - cache_creation - cache_read) * prices["input"]
            + cache_creation * prices["cache_write"]
            + cache_read * prices["cache_read"]
        ) / 1_000_000

        output_cost = (output_tokens * prices["output"]) / 1_000_000

        return input_cost + output_cost

    def report(self) -> dict:
        """전체 토큰 사용량 및 비용 보고서"""
        if not self.records:
            return {
                "total_tokens": 0,
                "total_cost": 0.0,
                "records": [],
            }

        total_input = sum(r["input_tokens"] for r in self.records)
        total_output = sum(r["output_tokens"] for r in self.records)
        total_cost = sum(r["cost_usd"] for r in self.records)

        by_node = {}
        for r in self.records:
            if r["node"] not in by_node:
                by_node[r["node"]] = 0.0
            by_node[r["node"]] += r["cost_usd"]

        top5_costly = sorted(by_node.items(), key=lambda x: -x[1])[:5]

        return {
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_tokens": total_input + total_output,
            "total_cost_usd": round(total_cost, 4),
            "average_cost_per_call": round(total_cost / max(len(self.records), 1), 4),
            "llm_calls": len(self.records),
            "top5_costly_nodes": top5_costly,
        }

    def recommend_optimizations(self) -> list[str]:
        """최적화 권장사항"""
        report = self.report()
        recs = []

        total_cost = report["total_cost_usd"]

        for node, cost in report["top5_costly_nodes"]:
            if cost > total_cost * 0.3:
                pct = (cost / total_cost) * 100
                recs.append(
                    f"📊 {node}: ${cost:.2f} ({pct:.0f}%) - "
                    f"모델 다운그레이드 또는 입력 축소 검토"
                )

        return recs
