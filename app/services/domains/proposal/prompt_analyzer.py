"""
프롬프트 패턴 분석 엔진 — 학습 사이클 2단계.

축적된 데이터(수정 이력, 리뷰 피드백, 수주/패찰)를 분석하여
"왜 이 프롬프트가 나쁜가"를 구조화.
"""

import logging
from datetime import date, timedelta

logger = logging.getLogger(__name__)


async def analyze_prompt(prompt_id: str, days: int = 90) -> dict:
    """프롬프트의 최근 N일 데이터를 종합 분석."""
    metrics = await _compute_metrics(prompt_id, days)
    edit_patterns = await classify_edit_patterns(prompt_id, limit=30)
    feedback = await _summarize_feedback(prompt_id, days)
    win_loss = await compare_win_loss(prompt_id)
    trend = await compute_trend(prompt_id, months=6)
    priority = _compute_priority(metrics)

    hypothesis = await _generate_hypothesis(
        prompt_id, metrics, edit_patterns, feedback, win_loss,
    )

    result = {
        "prompt_id": prompt_id,
        "metrics": metrics,
        "edit_patterns": edit_patterns,
        "feedback_summary": feedback,
        "win_loss_comparison": win_loss,
        "trend": trend,
        "hypothesis": hypothesis,
        "priority": priority,
    }

    # 스냅샷 저장
    await _save_snapshot(prompt_id, days, result)

    return result


async def classify_edit_patterns(prompt_id: str, limit: int = 30) -> list[dict]:
    """human_edit_tracking의 수정 diff를 AI로 패턴 분류."""
    try:
        from app.utils.supabase_client import get_async_client
        client = await get_async_client()

        edits = await (
            client.table("human_edit_tracking")
            .select("action, edit_ratio, section_id, original_text, edited_text")
            .eq("prompt_id", prompt_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )

        if not edits.data or len(edits.data) < 2:
            return []

        # 수정 유형 분류 (diff 기반)
        patterns: dict[str, dict] = {}
        for e in edits.data:
            original = e.get("original_text", "")
            edited = e.get("edited_text", "")

            if not original or not edited:
                # diff 없으면 action 기반 폴백
                cat = "전체 재작성" if e["action"] == "rewrite" else "부분 수정"
            else:
                cat = _categorize_diff(original, edited)

            if cat not in patterns:
                patterns[cat] = {"pattern": cat, "count": 0, "examples": []}
            patterns[cat]["count"] += 1
            if len(patterns[cat]["examples"]) < 2 and edited:
                patterns[cat]["examples"].append(edited[:100])

        result = sorted(patterns.values(), key=lambda x: x["count"], reverse=True)

        # 비율 계산
        total = sum(p["count"] for p in result)
        for p in result:
            p["pct"] = round(p["count"] / max(1, total) * 100, 1)

        return result[:10]
    except Exception as e:
        logger.warning("수정 패턴 분류 실패: %s", e)
        return []


def _categorize_diff(original: str, edited: str) -> str:
    """수정 전/후를 비교하여 수정 유형 분류 (규칙 기반)."""
    orig_len = len(original)
    edit_len = len(edited)
    ratio = edit_len / max(1, orig_len)

    # 분량 대폭 증가 → 내용 추가
    if ratio > 1.5:
        # 키워드로 추가 내용 유형 판별
        added = edited[orig_len:]
        if any(kw in added for kw in ["표", "Table", "|", "───"]):
            return "표/다이어그램 추가"
        if any(kw in added for kw in ["성능", "처리속도", "건/초", "%", "만원"]):
            return "성능 수치 보강"
        if any(kw in added for kw in ["구현", "코드", "API", "모듈", "클래스"]):
            return "구체적 구현 방법 추가"
        if any(kw in added for kw in ["비교", "대안", "vs", "선택 근거"]):
            return "기술 비교 추가"
        return "내용 보강 (기타)"

    # 분량 유사하지만 내용 변경 → 톤/표현 수정
    if 0.8 <= ratio <= 1.2:
        return "표현/톤 수정"

    # 분량 축소 → 간결화
    if ratio < 0.8:
        return "불필요 내용 삭제"

    return "기타 수정"


async def compare_win_loss(prompt_id: str) -> dict:
    """수주/패찰 제안서에서 이 프롬프트의 성능 비교."""
    try:
        from app.utils.supabase_client import get_async_client
        client = await get_async_client()

        # 프롬프트가 사용된 proposal_id 조회
        links = await (
            client.table("prompt_artifact_link")
            .select("proposal_id, quality_score")
            .eq("prompt_id", prompt_id)
            .execute()
        )
        if not links.data:
            return {}

        proposal_ids = list({lnk["proposal_id"] for lnk in links.data if lnk.get("proposal_id")})
        if not proposal_ids:
            return {}

        # 수주/패찰 결과 조회
        results = await (
            client.table("proposal_results")
            .select("proposal_id, result")
            .in_("proposal_id", proposal_ids[:50])
            .execute()
        )
        if not results.data:
            return {}

        result_map = {r["proposal_id"]: r["result"] for r in results.data}

        # quality_score를 수주/패찰로 분류
        win_scores = []
        loss_scores = []
        for lnk in links.data:
            pid = lnk.get("proposal_id")
            score = lnk.get("quality_score")
            if pid and score is not None and pid in result_map:
                if result_map[pid] == "won":
                    win_scores.append(score)
                elif result_map[pid] == "lost":
                    loss_scores.append(score)

        if not win_scores and not loss_scores:
            return {}

        win_avg = sum(win_scores) / len(win_scores) if win_scores else 0
        loss_avg = sum(loss_scores) / len(loss_scores) if loss_scores else 0

        differences = []
        if win_avg - loss_avg > 10:
            differences.append(f"수주 시 평균 품질 {win_avg:.1f}점 vs 패찰 시 {loss_avg:.1f}점 (차이 {win_avg - loss_avg:.1f}점)")

        return {
            "win_avg_quality": round(win_avg, 1),
            "loss_avg_quality": round(loss_avg, 1),
            "win_count": len(win_scores),
            "loss_count": len(loss_scores),
            "key_differences": differences,
        }
    except Exception as e:
        logger.warning("수주/패찰 비교 실패: %s", e)
        return {}


async def compute_trend(prompt_id: str, months: int = 6) -> list[dict]:
    """월별 추이 데이터."""
    try:
        from app.utils.supabase_client import get_async_client
        client = await get_async_client()

        # 최근 N개월 스냅샷 조회
        since = (date.today() - timedelta(days=months * 30)).isoformat()
        snapshots = await (
            client.table("prompt_analysis_snapshots")
            .select("period_end, avg_quality, avg_edit_ratio, win_rate")
            .eq("prompt_id", prompt_id)
            .gte("period_end", since)
            .order("period_end")
            .execute()
        )

        if snapshots.data:
            return [
                {
                    "period": s["period_end"][:7],  # YYYY-MM
                    "quality": s.get("avg_quality"),
                    "edit_ratio": s.get("avg_edit_ratio"),
                    "win_rate": s.get("win_rate"),
                }
                for s in snapshots.data
            ]

        # 스냅샷 없으면 prompt_artifact_link에서 직접 집계
        links = await (
            client.table("prompt_artifact_link")
            .select("quality_score, created_at")
            .eq("prompt_id", prompt_id)
            .gte("created_at", since)
            .order("created_at")
            .execute()
        )

        if not links.data:
            return []

        # 월별 그룹핑
        by_month: dict[str, list[float]] = {}
        for lnk in links.data:
            if lnk.get("quality_score") is None:
                continue
            month = lnk["created_at"][:7]
            if month not in by_month:
                by_month[month] = []
            by_month[month].append(lnk["quality_score"])

        return [
            {
                "period": month,
                "quality": round(sum(scores) / len(scores), 1),
                "edit_ratio": None,
                "win_rate": None,
            }
            for month, scores in sorted(by_month.items())
        ]
    except Exception as e:
        logger.warning("추이 계산 실패: %s", e)
        return []


def _compute_priority(metrics: dict) -> str:
    """개선 우선순위 판정."""
    edit_ratio = metrics.get("avg_edit_ratio", 0)
    quality = metrics.get("avg_quality", 100)
    win_rate = metrics.get("win_rate", 100)

    if edit_ratio > 0.5 and (quality < 75 or win_rate < 55):
        return "high"
    if edit_ratio > 0.35 or quality < 80:
        return "medium"
    return "low"


async def run_batch_analysis(top_n: int = 10) -> list[dict]:
    """전체 프롬프트 중 개선 필요 TOP N 선정 + 패턴 분석."""
    from app.services.domains.proposal.prompt_tracker import check_prompts_needing_attention

    attention = await check_prompts_needing_attention(
        edit_ratio_threshold=0.0, min_edits=1,
    )

    # 우선순위 높은 순 정렬
    sorted_prompts = sorted(
        attention,
        key=lambda x: (x.get("avg_edit_ratio", 0), -x.get("avg_quality_score", 100)),
        reverse=True,
    )

    results = []
    for item in sorted_prompts[:top_n]:
        pid = item.get("prompt_id", "")
        if not pid:
            continue
        try:
            analysis = await analyze_prompt(pid, days=90)
            # 사람 친화적 라벨 추가
            analysis["label"] = _prompt_id_to_label(pid)
            results.append(analysis)
        except Exception as e:
            logger.warning("배치 분석 실패 (%s): %s", pid, e)

    return results


# ── Private helpers ──

async def _compute_metrics(prompt_id: str, days: int) -> dict:
    """기본 수치 메트릭 계산."""
    from app.services.domains.proposal.prompt_tracker import compute_effectiveness
    metrics = await compute_effectiveness(prompt_id)
    return {
        "proposals_used": metrics.get("proposals_used", 0),
        "win_rate": metrics.get("win_rate"),
        "avg_quality": metrics.get("avg_quality_score"),
        "avg_edit_ratio": metrics.get("avg_edit_ratio"),
        "edit_count": metrics.get("edit_count", 0),
    }


async def _summarize_feedback(prompt_id: str, days: int) -> dict:
    """리뷰 피드백 키워드 추출."""
    from app.services.domains.proposal.prompt_evolution import _get_review_feedback_for_prompt
    raw = await _get_review_feedback_for_prompt(prompt_id)

    if not raw:
        return {"keywords": [], "themes": []}

    # 단순 키워드 빈도 (AI 분류 없이 규칙 기반)
    keywords_map: dict[str, int] = {}
    negative_phrases = [
        "근거 부족", "추상적", "구체성 부족", "수치 없음", "비교 없음",
        "톤 불일치", "분량 부족", "논리 약함", "RFP 미반영", "표 없음",
    ]
    for phrase in negative_phrases:
        count = raw.lower().count(phrase.lower())
        if count > 0:
            keywords_map[phrase] = count

    keywords = sorted(
        [{"word": k, "count": v} for k, v in keywords_map.items()],
        key=lambda x: x["count"], reverse=True,
    )

    return {"keywords": keywords, "themes": [k["word"] for k in keywords[:3]]}


async def _generate_hypothesis(
    prompt_id: str,
    metrics: dict,
    edit_patterns: list[dict],
    feedback: dict,
    win_loss: dict,
) -> str:
    """데이터 기반 개선 가설 생성."""
    parts = []

    if edit_patterns:
        top = edit_patterns[0]
        parts.append(f"가장 빈번한 수정 유형 '{top['pattern']}'({top['count']}건)을 프롬프트에 사전 지시로 추가")

    if feedback.get("themes"):
        parts.append(f"리뷰 피드백 '{', '.join(feedback['themes'][:2])}' 해소를 위한 지시 강화")

    if win_loss.get("key_differences"):
        parts.append(f"수주 제안서 특성({win_loss['key_differences'][0]}) 반영")

    if not parts:
        return "데이터 축적 후 가설 생성 가능"

    edit_ratio = metrics.get("avg_edit_ratio", 0)
    target = max(0.2, edit_ratio - 0.2)
    return f"{'; '.join(parts)}하면 수정율 {edit_ratio*100:.0f}% → {target*100:.0f}% 이하로 개선 가능"


async def _save_snapshot(prompt_id: str, days: int, result: dict) -> None:
    """분석 결과를 DB 스냅샷으로 저장."""
    try:
        from app.utils.supabase_client import get_async_client
        client = await get_async_client()

        metrics = result.get("metrics", {})
        today = date.today()
        await client.table("prompt_analysis_snapshots").insert({
            "prompt_id": prompt_id,
            "period_start": (today - timedelta(days=days)).isoformat(),
            "period_end": today.isoformat(),
            "proposals_used": metrics.get("proposals_used", 0),
            "win_count": result.get("win_loss_comparison", {}).get("win_count", 0),
            "loss_count": result.get("win_loss_comparison", {}).get("loss_count", 0),
            "win_rate": metrics.get("win_rate"),
            "avg_quality": metrics.get("avg_quality"),
            "avg_edit_ratio": metrics.get("avg_edit_ratio"),
            "edit_count": metrics.get("edit_count", 0),
            "edit_patterns": result.get("edit_patterns", []),
            "feedback_summary": result.get("feedback_summary", {}),
            "win_loss_diff": result.get("win_loss_comparison", {}),
            "hypothesis": result.get("hypothesis", ""),
            "priority": result.get("priority", "low"),
        }).execute()
    except Exception as e:
        logger.warning("분석 스냅샷 저장 실패: %s", e)


def _prompt_id_to_label(prompt_id: str) -> str:
    """프롬프트 ID를 사람 친화적 라벨로 변환."""
    labels = {
        "section_prompts.UNDERSTAND": "사업의 이해",
        "section_prompts.STRATEGY": "추진 전략",
        "section_prompts.METHODOLOGY": "수행 방법론",
        "section_prompts.TECHNICAL": "기술적 수행방안",
        "section_prompts.MANAGEMENT": "사업 관리",
        "section_prompts.PERSONNEL": "투입 인력",
        "section_prompts.TRACK_RECORD": "수행 실적",
        "section_prompts.SECURITY": "보안 대책",
        "section_prompts.MAINTENANCE": "유지보수/하자보수",
        "section_prompts.ADDED_VALUE": "부가제안/기대효과",
        "strategy.GENERATE_PROMPT": "전략 수립",
        "plan.STORY_PROMPT": "스토리라인 설계",
        "plan.PRICE_PROMPT": "예산/가격 전략",
        "plan.TEAM_PROMPT": "팀 구성",
        "proposal_prompts.SELF_REVIEW": "자가진단",
    }
    return labels.get(prompt_id, prompt_id.split(".")[-1].replace("_", " ").title())
