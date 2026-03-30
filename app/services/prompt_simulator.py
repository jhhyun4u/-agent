"""프롬프트 시뮬레이션 엔진 — 샌드박스 실행 + 품질 자가진단."""

import json
import logging
import os
import re
import time
from typing import Literal, Optional

from pydantic import BaseModel

logger = logging.getLogger(__name__)

DAILY_SIMULATION_LIMIT = 50
SIMULATION_MAX_TOKENS = 2000
QUALITY_CHECK_MAX_TOKENS = 500


class SimulationRequest(BaseModel):
    prompt_text: Optional[str] = None
    data_source: Literal["sample", "project", "custom"] = "sample"
    data_source_id: Optional[str] = None
    custom_variables: Optional[dict] = None
    run_quality_check: bool = True


class SimulationResult(BaseModel):
    simulation_id: Optional[str] = None
    output_text: str = ""
    tokens_input: int = 0
    tokens_output: int = 0
    duration_ms: int = 0
    model: str = ""
    quality_score: Optional[float] = None
    quality_detail: Optional[dict] = None
    variables_used: list[str] = []
    variables_missing: list[str] = []
    format_valid: bool = True
    format_errors: list[str] = []
    quota_remaining: int = 0


# ── 한도 관리 ──

async def check_quota(user_id: str) -> tuple[bool, int]:
    """일일 한도 체크. Returns: (허용 여부, 잔여 횟수)."""
    try:
        from app.utils.supabase_client import get_async_client
        client = await get_async_client()
        result = await (
            client.table("simulation_token_usage")
            .select("simulations_count")
            .eq("user_id", user_id)
            .eq("date", "today()")
            .limit(1)
            .execute()
        )
        used = result.data[0]["simulations_count"] if result.data else 0
        remaining = DAILY_SIMULATION_LIMIT - used
        return remaining > 0, max(0, remaining)
    except Exception:
        return True, DAILY_SIMULATION_LIMIT


async def get_quota_info(user_id: str) -> dict:
    """일일 한도 상세 정보."""
    try:
        from app.utils.supabase_client import get_async_client
        client = await get_async_client()
        result = await (
            client.table("simulation_token_usage")
            .select("simulations_count, tokens_input, tokens_output")
            .eq("user_id", user_id)
            .eq("date", "today()")
            .limit(1)
            .execute()
        )
        row = result.data[0] if result.data else {}
        used = row.get("simulations_count", 0)
        return {
            "daily_limit": DAILY_SIMULATION_LIMIT,
            "used_today": used,
            "remaining": max(0, DAILY_SIMULATION_LIMIT - used),
            "tokens_used_today": {
                "input": row.get("tokens_input", 0),
                "output": row.get("tokens_output", 0),
            },
        }
    except Exception:
        return {
            "daily_limit": DAILY_SIMULATION_LIMIT,
            "used_today": 0,
            "remaining": DAILY_SIMULATION_LIMIT,
            "tokens_used_today": {"input": 0, "output": 0},
        }


# ── 메인 실행 ──

async def run_simulation(
    prompt_id: str,
    req: SimulationRequest,
    user_id: str,
) -> SimulationResult:
    """시뮬레이션 메인 실행."""
    start = time.time()

    # 1. 프롬프트 텍스트 확보
    prompt_version = None
    if req.prompt_text:
        prompt_text = req.prompt_text
    else:
        from app.services.prompt_registry import get_active_prompt
        prompt_text, prompt_version, _ = await get_active_prompt(prompt_id)

    if not prompt_text:
        return SimulationResult(
            format_valid=False,
            format_errors=["프롬프트를 찾을 수 없습니다."],
        )

    # 2. state 데이터 로드
    state_data = await _load_state_data(
        req.data_source, req.data_source_id, req.custom_variables,
    )

    # 3. 변수 치환
    final_prompt, used, missing = _substitute_variables(prompt_text, state_data)

    # 4. Claude API 호출
    from app.services.claude_client import claude_generate
    output = await claude_generate(final_prompt, max_tokens=SIMULATION_MAX_TOKENS)
    output_text = (
        output if isinstance(output, str)
        else json.dumps(output, ensure_ascii=False, indent=2)
    )

    duration_ms = int((time.time() - start) * 1000)
    tokens_in = len(final_prompt) // 2
    tokens_out = len(output_text) // 2

    # 5. 출력 형식 검증
    format_valid, format_errors = _validate_output_format(prompt_id, output_text)

    # 6. 품질 자가진단 (선택)
    quality_score = None
    quality_detail = None
    if req.run_quality_check:
        quality_score, quality_detail = await _run_quality_check(
            prompt_id, output_text, state_data,
        )

    # 7. DB 저장 + 한도 업데이트
    sim_id = await _save_simulation(
        prompt_id, prompt_version, req, output_text,
        duration_ms, quality_score, quality_detail, user_id,
    )
    await _update_quota(user_id, tokens_in, tokens_out)

    _, remaining = await check_quota(user_id)

    return SimulationResult(
        simulation_id=sim_id,
        output_text=output_text,
        tokens_input=tokens_in,
        tokens_output=tokens_out,
        duration_ms=duration_ms,
        model="claude-sonnet-4-5-20250929",
        quality_score=quality_score,
        quality_detail=quality_detail,
        variables_used=used,
        variables_missing=missing,
        format_valid=format_valid,
        format_errors=format_errors,
        quota_remaining=remaining,
    )


async def run_comparison(
    prompt_id: str,
    version_a: Optional[int],
    text_a: Optional[str],
    version_b: Optional[int],
    text_b: Optional[str],
    data_source: str,
    data_source_id: Optional[str],
    run_quality_check: bool,
    user_id: str,
) -> dict:
    """A vs B 비교 시뮬레이션."""
    # version → text 변환
    if not text_a and version_a:
        text_a = await _get_prompt_by_version(prompt_id, version_a)
    if not text_b and version_b:
        text_b = await _get_prompt_by_version(prompt_id, version_b)

    req_a = SimulationRequest(
        prompt_text=text_a, data_source=data_source,
        data_source_id=data_source_id, run_quality_check=run_quality_check,
    )
    req_b = SimulationRequest(
        prompt_text=text_b, data_source=data_source,
        data_source_id=data_source_id, run_quality_check=run_quality_check,
    )

    result_a = await run_simulation(prompt_id, req_a, user_id)
    result_b = await run_simulation(prompt_id, req_b, user_id)

    q_diff = (result_b.quality_score or 0) - (result_a.quality_score or 0)
    t_diff = result_b.tokens_output - result_a.tokens_output
    d_diff = result_b.duration_ms - result_a.duration_ms

    if q_diff > 3:
        recommendation = f"B가 품질 +{q_diff:.1f}점 우수"
    elif q_diff < -3:
        recommendation = f"A가 품질 +{abs(q_diff):.1f}점 우수"
    else:
        recommendation = "유의미한 차이 없음"

    return {
        "result_a": result_a.model_dump(),
        "result_b": result_b.model_dump(),
        "comparison": {
            "quality_diff": round(q_diff, 1),
            "token_diff": t_diff,
            "duration_diff": d_diff,
            "recommendation": recommendation,
        },
    }


async def get_simulation_history(prompt_id: str, limit: int = 20) -> list[dict]:
    """시뮬레이션 이력 조회."""
    try:
        from app.utils.supabase_client import get_async_client
        client = await get_async_client()
        result = await (
            client.table("prompt_simulations")
            .select(
                "id, prompt_version, data_source, data_source_id, "
                "quality_score, output_meta, compared_with, created_at"
            )
            .eq("prompt_id", prompt_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data or []
    except Exception as e:
        logger.warning(f"시뮬레이션 이력 조회 실패: {e}")
        return []


# ── Private helpers ──

async def _get_prompt_by_version(prompt_id: str, version: int) -> Optional[str]:
    """특정 버전의 프롬프트 텍스트 조회."""
    try:
        from app.utils.supabase_client import get_async_client
        client = await get_async_client()
        result = await (
            client.table("prompt_registry")
            .select("content_text")
            .eq("prompt_id", prompt_id)
            .eq("version", version)
            .limit(1)
            .execute()
        )
        if result.data:
            return result.data[0]["content_text"]
    except Exception:
        pass
    return None


async def _load_state_data(
    source: str, source_id: Optional[str], custom: Optional[dict],
) -> dict:
    """시뮬레이션용 state 데이터 로드."""
    if source == "custom" and custom:
        return custom
    if source == "sample":
        return _load_sample_data(source_id or "sample_mid_consulting")
    if source == "project" and source_id:
        return await _load_project_state(source_id)
    return _load_sample_data("sample_mid_consulting")


def _load_sample_data(sample_id: str) -> dict:
    """샘플 RFP 데이터 로드."""
    sample_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "data", "sample_rfps", f"{sample_id}.json",
    )
    try:
        with open(sample_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"샘플 데이터 없음: {sample_path}, 기본값 사용")
        return _default_sample_state()


def _default_sample_state() -> dict:
    """기본 샘플 state (파일 없을 때 폴백)."""
    return {
        "rfp_text": "[샘플] 정보시스템 구축 용역 제안요청서. 사업 기간: 6개월, 예산: 3억원. "
                    "주요 요구사항: 현행 시스템 분석, 목표 시스템 설계, 구축 및 시험운영.",
        "rfp_analysis": {
            "project_name": "샘플 ISP",
            "budget": 300_000_000,
            "duration_months": 6,
            "eval_method": "기술+가격 분리평가",
            "eval_weights": {"기술": 90, "가격": 10},
            "key_requirements": ["현행 시스템 분석", "목표 시스템 설계", "구축 및 시험운영"],
            "compliance_items": ["참여 인력 자격", "유사 수행 실적", "보안 대책"],
        },
        "go_no_go": {"verdict": "go", "confidence": 85, "positioning": "offensive"},
        "strategy": {
            "win_theme": "고객 맞춤형 방법론과 검증된 수행 역량",
            "ghost_theme": "경쟁사 표준화 접근법의 한계",
            "positioning": "offensive",
            "differentiation": ["도메인 전문성", "애자일+워터폴 하이브리드"],
        },
        "positioning_guide": "공격적 포지셔닝: 차별화된 기술력과 도메인 전문성 강조",
        "prev_sections_context": "",
        "storyline_context": "",
    }


async def _load_project_state(project_id: str) -> dict:
    """기존 프로젝트의 state 스냅샷 로드."""
    try:
        from app.utils.supabase_client import get_async_client
        client = await get_async_client()
        result = await (
            client.table("proposals")
            .select("title, rfp_text, rfp_analysis, strategy, plan")
            .eq("id", project_id)
            .limit(1)
            .execute()
        )
        if result.data:
            row = result.data[0]
            return {
                "rfp_text": row.get("rfp_text", ""),
                "rfp_analysis": row.get("rfp_analysis", {}),
                "strategy": row.get("strategy", {}),
                "positioning_guide": "",
                "prev_sections_context": "",
                "storyline_context": "",
            }
    except Exception as e:
        logger.warning(f"프로젝트 state 로드 실패: {e}")
    return _default_sample_state()


def _substitute_variables(
    prompt_text: str, state: dict,
) -> tuple[str, list[str], list[str]]:
    """프롬프트 내 {변수}를 state 데이터로 치환."""
    # {{ }} 이스케이프 보호
    escaped = re.sub(r"\{\{(.*?)\}\}", lambda m: f"\x00L{m.group(1)}\x00R", prompt_text)

    variables = re.findall(r"\{(\w+)\}", escaped)
    used: list[str] = []
    missing: list[str] = []

    result = escaped
    for var in sorted(set(variables)):
        value = state.get(var)
        if value is not None:
            replacement = (
                json.dumps(value, ensure_ascii=False)
                if isinstance(value, (dict, list))
                else str(value)
            )
            result = result.replace(f"{{{var}}}", replacement)
            used.append(var)
        else:
            missing.append(var)
            result = result.replace(f"{{{var}}}", f"[미입력: {var}]")

    # 이스케이프 복원
    result = result.replace("\x00L", "{").replace("\x00R", "}")

    return result, used, missing


def _validate_output_format(prompt_id: str, output: str) -> tuple[bool, list[str]]:
    """출력 형식 기본 검증."""
    errors: list[str] = []

    json_prompts = {
        "strategy.GENERATE_PROMPT", "plan.TEAM_PROMPT", "plan.ASSIGN_PROMPT",
        "plan.SCHEDULE_PROMPT", "plan.STORY_PROMPT", "plan.PRICE_PROMPT",
        "proposal_prompts.SELF_REVIEW",
    }

    if prompt_id in json_prompts:
        try:
            json.loads(output)
        except json.JSONDecodeError:
            errors.append("JSON 형식이 아닙니다.")

    if len(output.strip()) < 50:
        errors.append("출력이 너무 짧습니다 (50자 미만).")

    return len(errors) == 0, errors


async def _run_quality_check(
    prompt_id: str, output: str, state: dict,
) -> tuple[Optional[float], Optional[dict]]:
    """간소화된 자가진단 (4축 100점)."""
    meta_prompt = f"""다음 AI 생성 결과물을 4개 축으로 평가하세요 (각 25점, 총 100점).

## 평가 대상
{output[:2000]}

## 원본 RFP 요약
{json.dumps(state.get("rfp_analysis", {}), ensure_ascii=False)[:500]}

## 평가 축
1. 적합성 (25점): RFP 요구사항 반영 정도
2. 전략 정합성 (25점): 전략/Win Theme과의 일관성
3. 품질 (25점): 구조, 깊이, 구체성
4. 신뢰성 (25점): 근거 제시, 과장 표현 없음

## 출력 (JSON만, 설명 없이)
{{"compliance": N, "strategy": N, "quality": N, "trustworthiness": N, "total": N}}"""

    try:
        from app.services.claude_client import claude_generate
        result = await claude_generate(meta_prompt, max_tokens=QUALITY_CHECK_MAX_TOKENS)
        if isinstance(result, dict):
            total = result.get("total", sum(
                result.get(k, 0)
                for k in ("compliance", "strategy", "quality", "trustworthiness")
            ))
            return float(total), result
        return None, None
    except Exception as e:
        logger.debug(f"품질 평가 실패: {e}")
        return None, None


async def _save_simulation(
    prompt_id: str,
    prompt_version: Optional[int],
    req: SimulationRequest,
    output_text: str,
    duration_ms: int,
    quality_score: Optional[float],
    quality_detail: Optional[dict],
    user_id: str,
) -> Optional[str]:
    """시뮬레이션 결과 DB 저장."""
    try:
        from app.utils.supabase_client import get_async_client
        client = await get_async_client()
        result = await client.table("prompt_simulations").insert({
            "prompt_id": prompt_id,
            "prompt_version": prompt_version,
            "prompt_text": req.prompt_text or "(active 버전)",
            "data_source": req.data_source,
            "data_source_id": req.data_source_id,
            "input_variables": req.custom_variables or {},
            "output_text": output_text,
            "output_meta": {
                "duration_ms": duration_ms,
                "model": "claude-sonnet-4-5-20250929",
            },
            "quality_score": quality_score,
            "quality_detail": quality_detail,
            "created_by": user_id,
        }).execute()
        return result.data[0]["id"] if result.data else None
    except Exception as e:
        logger.warning(f"시뮬레이션 저장 실패: {e}")
        return None


async def _update_quota(user_id: str, tokens_in: int, tokens_out: int):
    """일일 한도 업데이트 (upsert)."""
    try:
        from app.utils.supabase_client import get_async_client
        client = await get_async_client()
        await client.rpc("upsert_simulation_quota", {
            "p_user_id": user_id,
            "p_tokens_in": tokens_in,
            "p_tokens_out": tokens_out,
        }).execute()
    except Exception as e:
        logger.debug(f"한도 업데이트 실패: {e}")
