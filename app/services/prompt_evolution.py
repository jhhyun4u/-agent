"""
프롬프트 진화 엔진 — AI 개선 제안 + A/B 실험 + 자동 승격/롤백.

워크플로 내 추가 AI 호출 0건 — 진화 분석은 오프라인(수동/주간)으로만 실행.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


async def suggest_improvements(prompt_id: str) -> dict:
    """축적된 메트릭으로 Claude에게 개선 제안 요청 (~4K 토큰).

    Returns: {"suggestions": [{"title": str, "rationale": str, "prompt_text": str}]}
    """
    from app.services.prompt_tracker import compute_effectiveness

    # 현재 성과 데이터 수집
    metrics = await compute_effectiveness(prompt_id)

    # 현재 프롬프트 텍스트 조회
    from app.services.prompt_registry import get_active_prompt
    current_text, version, _ = await get_active_prompt(prompt_id)

    if not current_text:
        return {"error": f"프롬프트 '{prompt_id}' 를 찾을 수 없습니다."}

    # 빈출 수정 패턴 조회
    edit_patterns = await _get_frequent_edit_patterns(prompt_id)

    # 섹션별 품질 점수 패턴 조회 (Phase 3: 약점 패턴 분석)
    section_quality_patterns = await _get_section_quality_patterns(prompt_id)

    # 리뷰 피드백 텍스트 조회 (Human-in-the-Loop 정성적 신호)
    review_feedback_text = await _get_review_feedback_for_prompt(prompt_id)

    # 메타프롬프트
    meta_prompt = f"""다음 제안서 작성 프롬프트의 성과 데이터를 분석하고 개선안 3가지를 제시하세요.

## 현재 프롬프트 (v{version})
{current_text[:3000]}

## 성과 데이터
- 사용 횟수: {metrics.get('proposals_used', 0)}건
- 수주율: {metrics.get('win_rate', 'N/A')}%
- 평균 자가평가: {metrics.get('avg_quality_score', 'N/A')}점
- 평균 수정율: {metrics.get('avg_edit_ratio', 'N/A')} (0=무수정, 1=전체 재작성)
- 평균 토큰: 입력 {metrics.get('avg_input_tokens', 0)} / 출력 {metrics.get('avg_output_tokens', 0)}

## 빈출 수정 패턴 (사람이 자주 고치는 부분)
{edit_patterns or '(데이터 부족)'}

## 섹션별 품질 점수 패턴 (이 프롬프트로 생성된 섹션의 자가평가 점수)
{section_quality_patterns or '(섹션별 점수 데이터 부족)'}

## 사람 리뷰 피드백 (리뷰 게이트에서 사람이 남긴 구체적 피드백)
{review_feedback_text or '(리뷰 피드백 없음)'}

## 지시사항
1. 성과 데이터에서 약점을 파악하세요
2. 수정율이 높다면 → 프롬프트가 원하는 결과를 못 내고 있음
3. 섹션별 품질 점수가 낮은 패턴이 있다면 → 해당 약점을 보완하는 지시사항 강화
4. **사람 리뷰 피드백에서 반복되는 불만/요구를 분석하여 프롬프트에 반영하세요**
   - 예: "근거 부족" 반복 → 근거 제시 지시 강화
   - 예: "톤이 딱딱함" 반복 → 톤 가이드 추가
5. 각 개선안에 구체적 변경 이유 + 변경된 프롬프트 전문을 포함하세요
6. 토큰 효율성도 고려하세요 (불필요한 지시 축소)

## 출력 형식 (JSON)
{{
  "analysis": "현재 프롬프트 약점 분석 (2~3줄)",
  "suggestions": [
    {{
      "title": "개선안 제목",
      "rationale": "변경 이유",
      "key_changes": ["주요 변경 1", "주요 변경 2"],
      "prompt_text": "변경된 전체 프롬프트 텍스트"
    }}
  ]
}}"""

    from app.services.claude_client import claude_generate
    result = await claude_generate(meta_prompt, max_tokens=8000)

    return result


async def create_candidate(prompt_id: str, text: str, reason: str) -> Optional[int]:
    """후보 프롬프트 등록 (레지스트리 위임)."""
    from app.services.prompt_registry import register_candidate
    return await register_candidate(prompt_id, text, reason)


async def start_experiment(
    prompt_id: str,
    candidate_version: int,
    traffic_pct: int = 20,
    experiment_name: str = "",
    min_samples: int = 5,
) -> Optional[str]:
    """A/B 실험 시작."""
    try:
        from app.utils.supabase_client import get_async_client
        from app.services.prompt_registry import get_active_prompt

        client = await get_async_client()

        # 현재 활성 버전 → baseline
        _, baseline_version, _ = await get_active_prompt(prompt_id)
        if not baseline_version:
            return None

        if not experiment_name:
            experiment_name = f"{prompt_id} v{baseline_version} vs v{candidate_version}"

        result = await client.table("prompt_ab_experiments").insert({
            "experiment_name": experiment_name,
            "prompt_id": prompt_id,
            "baseline_version": baseline_version,
            "candidate_version": candidate_version,
            "traffic_pct": traffic_pct,
            "status": "running",
            "min_samples": min_samples,
        }).execute()

        if result.data:
            exp_id = result.data[0]["id"]
            logger.info(f"A/B 실험 시작: {experiment_name} (id={exp_id})")
            return exp_id
        return None
    except Exception as e:
        logger.error(f"실험 시작 실패: {e}")
        return None


async def evaluate_experiment(experiment_id: str) -> dict:
    """실험 결과 평가 — min_samples 도달 후 비교."""
    try:
        from app.utils.supabase_client import get_async_client
        from app.services.prompt_tracker import compute_effectiveness

        client = await get_async_client()

        # 실험 정보
        exp_result = await (
            client.table("prompt_ab_experiments")
            .select("*")
            .eq("id", experiment_id)
            .limit(1)
            .execute()
        )

        if not exp_result.data:
            return {"error": "실험을 찾을 수 없습니다."}

        exp = exp_result.data[0]

        if exp["status"] != "running":
            return {"error": f"실험이 '{exp['status']}' 상태입니다."}

        # 각 버전 성과
        baseline = await compute_effectiveness(exp["prompt_id"], exp["baseline_version"])
        candidate = await compute_effectiveness(exp["prompt_id"], exp["candidate_version"])

        baseline_n = baseline.get("proposals_used", 0)
        candidate_n = candidate.get("proposals_used", 0)

        evaluation = {
            "experiment_id": experiment_id,
            "experiment_name": exp["experiment_name"],
            "baseline": {
                "version": exp["baseline_version"],
                "samples": baseline_n,
                **baseline,
            },
            "candidate": {
                "version": exp["candidate_version"],
                "samples": candidate_n,
                **candidate,
            },
            "min_samples_reached": min(baseline_n, candidate_n) >= exp["min_samples"],
        }

        # 자동 판정
        if evaluation["min_samples_reached"]:
            b_score = _composite_score(baseline)
            c_score = _composite_score(candidate)
            improvement = c_score - b_score

            evaluation["baseline_composite"] = b_score
            evaluation["candidate_composite"] = c_score
            evaluation["improvement"] = round(improvement, 2)
            evaluation["recommendation"] = (
                "promote" if improvement >= exp["promote_threshold"] else
                "rollback" if improvement <= -exp["promote_threshold"] else
                "continue"
            )

        return evaluation
    except Exception as e:
        logger.error(f"실험 평가 실패: {e}")
        return {"error": str(e)}


async def promote_candidate(experiment_id: str) -> dict:
    """후보 프롬프트 → active 승격, 실험 종료."""
    try:
        from app.utils.supabase_client import get_async_client

        client = await get_async_client()

        exp_result = await (
            client.table("prompt_ab_experiments")
            .select("*")
            .eq("id", experiment_id)
            .limit(1)
            .execute()
        )

        if not exp_result.data:
            return {"error": "실험을 찾을 수 없습니다."}

        exp = exp_result.data[0]

        # 기존 active → retired
        await (
            client.table("prompt_registry")
            .update({"status": "retired"})
            .eq("prompt_id", exp["prompt_id"])
            .eq("status", "active")
            .execute()
        )

        # candidate → active
        await (
            client.table("prompt_registry")
            .update({"status": "active"})
            .eq("prompt_id", exp["prompt_id"])
            .eq("version", exp["candidate_version"])
            .execute()
        )

        # 실험 완료
        await (
            client.table("prompt_ab_experiments")
            .update({
                "status": "completed",
                "conclusion": "후보 승격",
                "promoted_version": exp["candidate_version"],
                "ended_at": "now()",
            })
            .eq("id", experiment_id)
            .execute()
        )

        logger.info(f"프롬프트 승격: {exp['prompt_id']} v{exp['candidate_version']}")
        return {"promoted": True, "version": exp["candidate_version"]}
    except Exception as e:
        logger.error(f"승격 실패: {e}")
        return {"error": str(e)}


async def rollback_experiment(experiment_id: str) -> dict:
    """실험 롤백 — 후보 retired, 실험 종료."""
    try:
        from app.utils.supabase_client import get_async_client

        client = await get_async_client()

        exp_result = await (
            client.table("prompt_ab_experiments")
            .select("*")
            .eq("id", experiment_id)
            .limit(1)
            .execute()
        )

        if not exp_result.data:
            return {"error": "실험을 찾을 수 없습니다."}

        exp = exp_result.data[0]

        # candidate → retired
        await (
            client.table("prompt_registry")
            .update({"status": "retired"})
            .eq("prompt_id", exp["prompt_id"])
            .eq("version", exp["candidate_version"])
            .execute()
        )

        # 실험 종료
        await (
            client.table("prompt_ab_experiments")
            .update({
                "status": "rolled_back",
                "conclusion": "후보 롤백 — baseline 유지",
                "ended_at": "now()",
            })
            .eq("id", experiment_id)
            .execute()
        )

        logger.info(f"실험 롤백: {exp['prompt_id']}")
        return {"rolled_back": True}
    except Exception as e:
        logger.error(f"롤백 실패: {e}")
        return {"error": str(e)}


def _composite_score(metrics: dict) -> float:
    """복합 점수 계산 (수주율 50% + 자가평가 30% + 수정율 역수 20%)."""
    win_rate = metrics.get("win_rate") or 0
    quality = metrics.get("avg_quality_score") or 0
    edit_ratio = metrics.get("avg_edit_ratio") or 0

    return round(
        win_rate * 0.5
        + quality * 0.3
        + (1 - edit_ratio) * 100 * 0.2,
        2
    )


async def _get_review_feedback_for_prompt(prompt_id: str) -> str:
    """이 프롬프트와 관련된 리뷰 게이트 피드백 텍스트 수집.

    prompt_artifact_link → proposal_id → feedbacks 테이블 조인.
    """
    try:
        from app.utils.supabase_client import get_async_client

        client = await get_async_client()

        # 이 프롬프트가 사용된 proposal_id 목록
        links = await (
            client.table("prompt_artifact_link")
            .select("proposal_id, artifact_step")
            .eq("prompt_id", prompt_id)
            .order("created_at", desc=True)
            .limit(20)
            .execute()
        )

        if not links.data:
            return ""

        proposal_ids = list({l["proposal_id"] for l in links.data})
        # 프롬프트가 사용된 step 파악 (section_prompts → proposal/section, strategy → strategy 등)
        steps = list({l["artifact_step"] for l in links.data})

        # 해당 proposal의 피드백 조회
        feedbacks = await (
            client.table("feedbacks")
            .select("step, feedback, comments, created_at")
            .in_("proposal_id", proposal_ids[:10])
            .order("created_at", desc=True)
            .limit(20)
            .execute()
        )

        if not feedbacks.data:
            return ""

        # 관련 step의 피드백만 필터 (section_prompts → "section"/"proposal" step)
        step_mapping = {
            "proposal_write_next": ["section", "proposal"],
            "self_review": ["proposal"],
            "strategy_generate": ["strategy"],
            "plan_team": ["plan"], "plan_assign": ["plan"],
            "plan_schedule": ["plan"], "plan_story": ["plan"],
            "plan_price": ["plan"],
            "presentation_strategy": ["ppt"],
            "ppt_toc": ["ppt"], "ppt_visual_brief": ["ppt"],
            "ppt_storyboard": ["ppt"],
        }
        relevant_steps = set()
        for s in steps:
            relevant_steps.update(step_mapping.get(s, [s]))

        filtered = [
            f for f in feedbacks.data
            if f.get("step") in relevant_steps and f.get("feedback")
        ]

        if not filtered:
            return ""

        parts = []
        for f in filtered[:10]:
            text = f["feedback"]
            if len(text) > 200:
                text = text[:200] + "..."
            parts.append(f"- [{f['step']}] {text}")

            # comments가 있으면 키별로 추가
            comments = f.get("comments")
            if isinstance(comments, dict):
                for key, val in list(comments.items())[:3]:
                    parts.append(f"  > {key}: {val}")

        return "\n".join(parts)
    except Exception:
        return ""


async def _get_section_quality_patterns(prompt_id: str) -> str:
    """이 프롬프트로 생성된 섹션의 품질 점수 패턴 분석."""
    try:
        from app.utils.supabase_client import get_async_client

        client = await get_async_client()

        links = await (
            client.table("prompt_artifact_link")
            .select("section_id, quality_score, proposal_id")
            .eq("prompt_id", prompt_id)
            .order("created_at", desc=True)
            .limit(50)
            .execute()
        )

        if not links.data:
            return ""

        # 품질 점수가 있는 것만 필터
        scored = [l for l in links.data if l.get("quality_score") is not None]
        if not scored:
            return ""

        # 전체 평균
        avg_all = sum(l["quality_score"] for l in scored) / len(scored)

        # 섹션별 집계
        by_section: dict = {}
        for l in scored:
            sid = l.get("section_id", "unknown")
            if sid not in by_section:
                by_section[sid] = []
            by_section[sid].append(l["quality_score"])

        parts = [f"전체 평균 품질: {avg_all:.1f}점 ({len(scored)}건)"]

        # 약한 섹션 (평균 70 미만) 하이라이트
        weak_sections = []
        for sid, scores in sorted(by_section.items()):
            avg = sum(scores) / len(scores)
            marker = " ⚠ 약점" if avg < 70 else ""
            parts.append(f"- {sid}: 평균 {avg:.1f}점 ({len(scores)}건){marker}")
            if avg < 70:
                weak_sections.append(sid)

        if weak_sections:
            parts.append(f"\n반복적 약점 섹션: {', '.join(weak_sections)}")

        return "\n".join(parts)
    except Exception:
        return ""


async def _get_frequent_edit_patterns(prompt_id: str) -> str:
    """빈출 수정 패턴 요약."""
    try:
        from app.utils.supabase_client import get_async_client

        client = await get_async_client()

        edits = await (
            client.table("human_edit_tracking")
            .select("action, edit_ratio, section_id")
            .eq("prompt_id", prompt_id)
            .order("created_at", desc=True)
            .limit(20)
            .execute()
        )

        if not edits.data:
            return ""

        # 행동별 집계
        actions = {}
        for e in edits.data:
            a = e["action"]
            actions[a] = actions.get(a, 0) + 1

        avg_ratio = sum(e.get("edit_ratio", 0) for e in edits.data) / len(edits.data)

        parts = [f"행동 분포: {actions}", f"평균 수정율: {avg_ratio:.3f}"]
        return "\n".join(parts)
    except Exception:
        return ""
