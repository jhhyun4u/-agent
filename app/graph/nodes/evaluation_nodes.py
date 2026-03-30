"""
v4.0: 모의 평가 + 평가결과 + Closing 노드 (6A, 7, 8)

6A — mock_evaluation: 제안서 + PPT 완성 후 모의 평가 시뮬레이션
7  — eval_result: 실제 평가 결과 기록 (입력 대기)
8  — project_closing: 프로젝트 종료 처리 (KB 업데이트, 아카이브)
"""

import asyncio
import logging

from app.graph.state import ProposalState
from app.services.claude_client import claude_generate

logger = logging.getLogger(__name__)


# ── 6A: 모의 평가 ──

async def mock_evaluation(state: ProposalState) -> dict:
    """제안서 + PPT를 바탕으로 평가위원 3인의 모의 평가 시뮬레이션."""
    rfp = state.get("rfp_analysis")
    rfp_dict = rfp.model_dump() if hasattr(rfp, "model_dump") else (rfp if isinstance(rfp, dict) else {})
    strategy = state.get("strategy")
    strategy_dict = strategy.model_dump() if hasattr(strategy, "model_dump") else (strategy if isinstance(strategy, dict) else {})
    sections = state.get("proposal_sections", [])
    eval_sim = state.get("evaluation_simulation", {})

    # 섹션 요약 (토큰 절약)
    section_summaries = []
    for s in sections[:15]:
        sd = s.model_dump() if hasattr(s, "model_dump") else (s if isinstance(s, dict) else {})
        section_summaries.append({
            "title": sd.get("title", ""),
            "content_preview": sd.get("content", "")[:300],
        })

    eval_items = rfp_dict.get("eval_items", [])

    prompt = f"""다음 제안서를 3명의 모의 평가위원 관점에서 평가하세요.

## 평가항목
{eval_items}

## 제안 전략
- Win Theme: {strategy_dict.get('win_theme', '')}
- 포지셔닝: {strategy_dict.get('positioning', '')}

## 제안서 섹션 ({len(section_summaries)}개)
{section_summaries}

## 기존 자가진단 결과
{eval_sim}

## 출력 형식 (JSON)
{{
  "evaluators": [
    {{
      "role": "기술 전문가",
      "scores": [
        {{"item": "평가항목명", "max_score": 30, "given_score": 25, "comment": "평가 코멘트"}}
      ],
      "total_score": 85,
      "overall_comment": "종합 의견"
    }}
  ],
  "aggregate": {{
    "average_score": 0,
    "min_score": 0,
    "max_score": 0,
    "win_probability": "높음|보통|낮음",
    "strengths": ["강점 1", "강점 2"],
    "weaknesses": ["약점 1", "약점 2"],
    "improvement_suggestions": ["개선 제안 1"]
  }},
  "risk_assessment": "수주 가능성에 대한 총평"
}}
"""

    try:
        result = await claude_generate(
            prompt=prompt,
            system_prompt="당신은 공공기관 평가위원 경력 20년의 전문가입니다. 실제 평가 기준에 따라 엄격하고 공정하게 평가하세요.",
            response_format="json",
            temperature=0.4,
        )
        return {
            "mock_evaluation_result": result,
            "current_step": "mock_evaluation_complete",
        }
    except Exception as e:
        logger.error(f"mock_evaluation 실패: {e}")
        return {
            "mock_evaluation_result": {"error": str(e)},
            "current_step": "mock_evaluation_error",
        }


# ── 7: 평가결과 ──

async def eval_result_node(state: ProposalState) -> dict:
    """평가결과 기록 노드.

    실제 결과는 사용자가 리뷰 시 입력 (interrupt).
    mock_evaluation_result를 기본값으로 표시.
    """
    mock = state.get("mock_evaluation_result", {})

    # 기존 결과가 있으면 그대로 유지
    existing = state.get("eval_result")
    if existing:
        return {"current_step": "eval_result_recorded"}

    # 기본값: 모의 평가 결과 기반
    return {
        "eval_result": {
            "source": "mock_evaluation",
            "mock_average_score": mock.get("aggregate", {}).get("average_score"),
            "mock_win_probability": mock.get("aggregate", {}).get("win_probability"),
            "actual_result": None,  # 사용자가 리뷰에서 입력
            "actual_score": None,
            "actual_rank": None,
            "lessons_learned": [],
        },
        "current_step": "eval_result_pending",
    }


# ── 8: Closing ──

async def project_closing(state: ProposalState) -> dict:
    """프로젝트 종료 처리.

    - KB 업데이트 트리거 (수주/패찰 결과 기반)
    - 교훈 아카이브
    - 프로젝트 상태 → closed
    """
    proposal_id = state.get("project_id", "")
    eval_data = state.get("eval_result", {})
    actual_result = eval_data.get("actual_result")  # won / lost / None

    # KB 업데이트 (비동기 fire-and-forget)
    if actual_result and proposal_id:
        _fire_kb_update(proposal_id, actual_result, state)

    # 프로젝트 상태 업데이트
    if proposal_id:
        _fire_status_update(proposal_id, actual_result)

    return {
        "project_closing_result": {
            "status": "closed",
            "actual_result": actual_result,
            "kb_updated": actual_result is not None,
            "lessons_count": len(eval_data.get("lessons_learned", [])),
        },
        "current_step": "project_closed",
    }


def _fire_kb_update(proposal_id: str, result: str, state: ProposalState) -> None:
    """수주/패찰 결과를 KB에 반영 (fire-and-forget)."""
    async def _update():
        try:
            from app.services.kb_updater import update_from_result
            await update_from_result(proposal_id, result, state)
        except Exception as e:
            logger.warning(f"KB 업데이트 실패 (무시): {e}")

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_update())
    except RuntimeError:
        pass


def _fire_status_update(proposal_id: str, result: str | None) -> None:
    """proposals 테이블 상태를 closed/won/lost로 업데이트."""
    async def _update():
        try:
            from app.utils.supabase_client import get_async_client
            client = await get_async_client()
            status = "won" if result == "won" else "lost" if result == "lost" else "completed"
            await client.table("proposals").update({
                "status": status,
                "current_phase": "closed",
            }).eq("id", proposal_id).execute()
        except Exception as e:
            logger.warning(f"프로젝트 상태 업데이트 실패: {e}")

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_update())
    except RuntimeError:
        pass
