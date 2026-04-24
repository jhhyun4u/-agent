"""
Pre-Flight Check — Claude API 호출 전 프롬프트 검증.

완성된 프롬프트의 품질을 사전 검증하여
빈 데이터/토큰 초과/필수 컨텍스트 누락을 차단.
"""

import logging
import re
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# ── 빈 데이터 폴백 패턴 ──
EMPTY_FALLBACK_PATTERNS = [
    r"\([\w\s]*없음[\w\s]*\)",    # (역량 DB 없음), (경쟁사 정보 없음) 등
    r"\([\w\s]*미수행[\w\s]*\)",   # (리서치 미수행)
    r"\([\w\s]*미도출[\w\s]*\)",   # (미도출)
    r"\([\w\s]*부족[\w\s]*\)",     # (데이터 부족)
    r"\(첫 번째 제안\)",
]
_EMPTY_RE = re.compile("|".join(EMPTY_FALLBACK_PATTERNS))

# ── None/빈 치환 패턴 ──
NONE_PATTERNS = re.compile(
    r"(?:^|\n)\s*(?:None|\[\]|\{\}|\"\")\s*(?:\n|$)", re.MULTILINE
)

# ── 노드별 토큰 예산 (입력 기준, 대략적 한글 1char ≈ 0.5token) ──
STEP_TOKEN_BUDGETS: dict[str, int] = {
    "strategy_generate": 25_000,
    "go_no_go": 15_000,
    "plan_team": 10_000,
    "plan_assign": 10_000,
    "plan_schedule": 10_000,
    "plan_story": 20_000,
    "plan_price": 15_000,
    "proposal_write_next": 30_000,
    "self_review": 40_000,
    "ppt_toc": 15_000,
    "ppt_visual_brief": 15_000,
    "ppt_storyboard": 40_000,
    "rfp_search": 10_000,
    "rfp_analyze": 20_000,
    "research_gather": 15_000,
}

# ── 노드별 필수 컨텍스트 (이 변수가 비어있으면 차단/경고) ──
REQUIRED_CONTEXT: dict[str, list[str]] = {
    "strategy_generate": ["rfp_summary", "positioning"],
    "go_no_go": ["rfp_summary"],
    "plan_story": ["rfp_summary", "positioning", "win_theme"],
    "plan_price": ["rfp_summary", "budget"],
    "proposal_write_next": ["rfp_summary", "positioning", "win_theme"],
    "self_review": ["sections_summary"],
}


@dataclass
class PreFlightResult:
    """검증 결과."""
    passed: bool = True
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    empty_ratio: float = 0.0
    estimated_tokens: int = 0
    token_budget: int = 0
    none_substitutions: int = 0


def check_prompt(
    prompt: str,
    step_name: str = "",
    variables: dict[str, str] | None = None,
) -> PreFlightResult:
    """완성된 프롬프트의 품질을 사전 검증.

    Args:
        prompt: .format() 완료된 최종 프롬프트 텍스트
        step_name: 노드 이름 (토큰 예산 조회용)
        variables: 치환에 사용된 변수 dict (선택 — 상세 분석용)

    Returns:
        PreFlightResult: 검증 결과 (passed=False면 호출 중단 권장)
    """
    result = PreFlightResult()

    # ── 1. 빈 데이터 폴백 비율 ──
    empty_matches = _EMPTY_RE.findall(prompt)
    result.empty_ratio = len(empty_matches) / max(1, len(prompt.split("\n"))) * 10
    if result.empty_ratio > 0.5:
        result.warnings.append(
            f"빈 데이터 비율 높음: {len(empty_matches)}건 ({result.empty_ratio:.0%}). "
            f"패턴: {empty_matches[:3]}"
        )
    if result.empty_ratio > 0.8:
        result.errors.append(
            f"빈 데이터 과다: {len(empty_matches)}건. 핵심 컨텍스트 대부분 누락."
        )
        result.passed = False

    # ── 2. None/빈 치환 감지 ──
    none_matches = NONE_PATTERNS.findall(prompt)
    result.none_substitutions = len(none_matches)
    if none_matches:
        result.warnings.append(
            f"None/빈값 치환 {len(none_matches)}건 감지: "
            f"{[m.strip()[:20] for m in none_matches[:3]]}"
        )

    # ── 3. 토큰 예산 체크 ──
    result.estimated_tokens = len(prompt) // 2  # 한글+영문 혼합 근사
    result.token_budget = STEP_TOKEN_BUDGETS.get(step_name, 30_000)
    if result.estimated_tokens > result.token_budget:
        result.warnings.append(
            f"토큰 예산 초과: ~{result.estimated_tokens:,} > {result.token_budget:,} "
            f"({step_name}). 출력 품질 저하 가능."
        )
    if result.estimated_tokens > result.token_budget * 1.5:
        result.errors.append(
            f"토큰 대폭 초과: ~{result.estimated_tokens:,} > "
            f"{result.token_budget:,} × 1.5. 컨텍스트 축소 필요."
        )

    # ── 4. 필수 컨텍스트 존재 확인 ──
    required = REQUIRED_CONTEXT.get(step_name, [])
    if variables:
        for key in required:
            val = variables.get(key, "")
            if not val or val.strip() in ("", "None", "[]", "{}", "(없음)"):
                result.errors.append(f"필수 컨텍스트 누락: {key} (step={step_name})")
                result.passed = False

    # ── 5. 미치환 변수 잔존 ──
    unresolved = re.findall(r"\{(\w+)\}", prompt)
    # JSON 출력 형식 블록 안의 변수는 제외 ({{ }} 이스케이프)
    # 실제 미치환은 단독 {var} 형태
    if unresolved:
        # 출력 형식 내의 변수 필터링 (section_id 등 JSON 템플릿 변수 제외)
        json_template_vars = {
            "section_id", "slide_id", "bid_no", "bid_title", "agency",
        }
        real_unresolved = [v for v in unresolved if v not in json_template_vars]
        if real_unresolved:
            result.warnings.append(
                f"미치환 변수 {len(real_unresolved)}건: {real_unresolved[:5]}"
            )

    # ── 로깅 ──
    if result.errors:
        logger.warning(
            "[PreFlight FAIL] step=%s errors=%s warnings=%s tokens=~%d",
            step_name, result.errors, result.warnings, result.estimated_tokens,
        )
    elif result.warnings:
        logger.info(
            "[PreFlight WARN] step=%s warnings=%s tokens=~%d",
            step_name, result.warnings, result.estimated_tokens,
        )

    return result
