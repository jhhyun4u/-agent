"""
프롬프트 성과 추적 서비스 — 노드별 프롬프트 사용 기록 + 성과 집계.

Phase B: 프롬프트→산출물 귀속 (prompt_artifact_link).
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


async def record_usage(
    proposal_id: str,
    artifact_step: str,
    section_id: Optional[str],
    prompt_id: str,
    prompt_version: int,
    prompt_hash: str,
    input_tokens: int = 0,
    output_tokens: int = 0,
    duration_ms: int = 0,
    quality_score: Optional[float] = None,
) -> None:
    """프롬프트 사용 기록을 prompt_artifact_link에 삽입."""
    try:
        from app.utils.supabase_client import get_async_client

        client = await get_async_client()
        await client.table("prompt_artifact_link").insert({
            "proposal_id": proposal_id,
            "artifact_step": artifact_step,
            "section_id": section_id,
            "prompt_id": prompt_id,
            "prompt_version": prompt_version,
            "prompt_hash": prompt_hash,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "duration_ms": duration_ms,
            "quality_score": quality_score,
        }).execute()
    except Exception as e:
        logger.warning(f"프롬프트 사용 기록 실패 (무시): {e}")


async def record_usage_from_token_summary(
    proposal_id: str,
    artifact_step: str,
    section_id: Optional[str],
    prompt_id: str,
    prompt_version: int,
    prompt_hash: str,
    token_summary: dict,
) -> None:
    """토큰 요약 딕셔너리에서 사용량 추출하여 기록."""
    await record_usage(
        proposal_id=proposal_id,
        artifact_step=artifact_step,
        section_id=section_id,
        prompt_id=prompt_id,
        prompt_version=prompt_version,
        prompt_hash=prompt_hash,
        input_tokens=token_summary.get("input_tokens", 0),
        output_tokens=token_summary.get("output_tokens", 0),
        duration_ms=token_summary.get("duration_ms", 0),
    )


async def compute_effectiveness(prompt_id: str, prompt_version: Optional[int] = None) -> dict:
    """특정 프롬프트(버전)의 성과 메트릭 계산."""
    try:
        from app.utils.supabase_client import get_async_client

        client = await get_async_client()
        query = (
            client.table("prompt_artifact_link")
            .select("proposal_id, quality_score, input_tokens, output_tokens, duration_ms")
            .eq("prompt_id", prompt_id)
        )
        if prompt_version is not None:
            query = query.eq("prompt_version", prompt_version)

        result = await query.execute()
        rows = result.data or []

        if not rows:
            return {"proposals_used": 0}

        proposal_ids = list({r["proposal_id"] for r in rows})

        # 수주 결과 조회
        results = await (
            client.table("proposal_results")
            .select("proposal_id, result")
            .in_("proposal_id", proposal_ids)
            .execute()
        )
        result_map = {r["proposal_id"]: r["result"] for r in (results.data or [])}

        won = sum(1 for pid in proposal_ids if result_map.get(pid) == "won")
        lost = sum(1 for pid in proposal_ids if result_map.get(pid) == "lost")
        total_decided = won + lost

        quality_scores = [r["quality_score"] for r in rows if r.get("quality_score")]

        # 사람 수정율 조회
        edits = await (
            client.table("human_edit_tracking")
            .select("edit_ratio")
            .eq("prompt_id", prompt_id)
            .execute()
        )
        edit_ratios = [e["edit_ratio"] for e in (edits.data or []) if e.get("edit_ratio") is not None]

        return {
            "prompt_id": prompt_id,
            "prompt_version": prompt_version,
            "proposals_used": len(proposal_ids),
            "won": won,
            "lost": lost,
            "win_rate": round(won / total_decided * 100, 1) if total_decided else None,
            "avg_quality_score": round(sum(quality_scores) / len(quality_scores), 2) if quality_scores else None,
            "avg_edit_ratio": round(sum(edit_ratios) / len(edit_ratios), 4) if edit_ratios else None,
            "avg_input_tokens": round(sum(r.get("input_tokens", 0) for r in rows) / len(rows)) if rows else 0,
            "avg_output_tokens": round(sum(r.get("output_tokens", 0) for r in rows) / len(rows)) if rows else 0,
            "avg_duration_ms": round(sum(r.get("duration_ms", 0) for r in rows) / len(rows)) if rows else 0,
        }
    except Exception as e:
        logger.error(f"성과 메트릭 계산 실패: {e}")
        return {"error": str(e)}


async def refresh_materialized_view() -> bool:
    """mv_prompt_effectiveness 갱신."""
    try:
        from app.utils.supabase_client import get_async_client

        client = await get_async_client()
        await client.rpc("refresh_mv_prompt_effectiveness").execute()
        return True
    except Exception as e:
        logger.warning(f"MV 갱신 실패 (무시): {e}")
        return False


async def check_prompts_needing_attention(edit_ratio_threshold: float = 0.5, min_edits: int = 3) -> list[dict]:
    """수정율이 높은 프롬프트를 감지하여 개선 필요 목록 반환.

    Phase 2: 주기적 점검 + 알림 트리거.
    Returns: [{"prompt_id": str, "avg_edit_ratio": float, "edit_count": int, "action": str}]
    """
    try:
        from app.utils.supabase_client import get_async_client

        client = await get_async_client()
        edits = await (
            client.table("human_edit_tracking")
            .select("prompt_id, edit_ratio")
            .execute()
        )

        if not edits.data:
            return []

        # prompt_id별 집계
        stats: dict = {}
        for e in edits.data:
            pid = e.get("prompt_id")
            if not pid:
                continue
            if pid not in stats:
                stats[pid] = {"ratios": [], "count": 0}
            stats[pid]["count"] += 1
            if e.get("edit_ratio") is not None:
                stats[pid]["ratios"].append(e["edit_ratio"])

        attention = []
        for pid, s in stats.items():
            if s["count"] < min_edits:
                continue
            avg_ratio = sum(s["ratios"]) / len(s["ratios"]) if s["ratios"] else 0
            if avg_ratio >= edit_ratio_threshold:
                attention.append({
                    "prompt_id": pid,
                    "avg_edit_ratio": round(avg_ratio, 4),
                    "edit_count": s["count"],
                    "action": "suggest_improvement",
                })

        return sorted(attention, key=lambda x: x["avg_edit_ratio"], reverse=True)
    except Exception as e:
        logger.error(f"주의 프롬프트 점검 실패: {e}")
        return []


async def periodic_maintenance() -> dict:
    """주기적 유지보수: MV 갱신 + 주의 프롬프트 감지 + A/B 실험 자동 평가.

    main.py lifespan 또는 스케줄러에서 호출.
    """
    results = {"mv_refreshed": False, "attention_prompts": [], "experiments_evaluated": []}

    # 1. Materialized View 갱신
    results["mv_refreshed"] = await refresh_materialized_view()

    # 2. 주의 프롬프트 감지
    attention = await check_prompts_needing_attention()
    results["attention_prompts"] = attention

    # 3. A/B 실험 자동 평가
    try:
        from app.utils.supabase_client import get_async_client
        from app.services.domains.proposal.prompt_evolution import evaluate_experiment, promote_candidate, rollback_experiment

        client = await get_async_client()
        running = await (
            client.table("prompt_ab_experiments")
            .select("id, experiment_name, prompt_id")
            .eq("status", "running")
            .execute()
        )

        for exp in (running.data or []):
            try:
                eval_result = await evaluate_experiment(exp["id"])
                if eval_result.get("min_samples_reached"):
                    rec = eval_result.get("recommendation")
                    if rec == "promote":
                        await promote_candidate(exp["id"])
                        results["experiments_evaluated"].append({
                            "id": exp["id"], "action": "promoted"
                        })
                        logger.info(f"A/B 실험 자동 승격: {exp['experiment_name']}")
                    elif rec == "rollback":
                        await rollback_experiment(exp["id"])
                        results["experiments_evaluated"].append({
                            "id": exp["id"], "action": "rolled_back"
                        })
                        logger.info(f"A/B 실험 자동 롤백: {exp['experiment_name']}")
                    else:
                        results["experiments_evaluated"].append({
                            "id": exp["id"], "action": "continue"
                        })
            except Exception as e:
                logger.debug(f"실험 {exp['id']} 평가 실패: {e}")
    except Exception as e:
        logger.warning(f"A/B 실험 자동 평가 실패: {e}")

    # 4. 주의 프롬프트 → 자동 개선 제안 생성 + 후보 등록 + A/B 실험 시작
    results["auto_improvements"] = []
    if attention:
        try:
            from app.services.domains.proposal.prompt_evolution import suggest_improvements, create_candidate, start_experiment

            for a in attention[:3]:  # 상위 3개만 자동 처리
                pid = a["prompt_id"]
                # _inline 프롬프트는 자동 개선 대상 제외
                if pid.startswith("_inline."):
                    continue
                try:
                    suggestions = await suggest_improvements(pid)
                    if suggestions.get("suggestions"):
                        best = suggestions["suggestions"][0]
                        # 후보 등록
                        new_ver = await create_candidate(
                            pid, best["prompt_text"],
                            f"자동 개선: {best['title']}"
                        )
                        if new_ver:
                            # A/B 실험 자동 시작 (20% 트래픽)
                            exp_id = await start_experiment(
                                pid, new_ver, traffic_pct=20,
                                experiment_name=f"[자동] {pid} — {best['title']}"
                            )
                            results["auto_improvements"].append({
                                "prompt_id": pid,
                                "candidate_version": new_ver,
                                "experiment_id": exp_id,
                                "reason": best["title"],
                            })
                            logger.info(f"자동 프롬프트 개선: {pid} v{new_ver} → A/B 실험 시작")
                except Exception as e:
                    logger.debug(f"자동 개선 실패 ({pid}): {e}")
        except Exception as e:
            logger.warning(f"자동 프롬프트 개선 실패: {e}")

    # 5. Teams 알림 (주의 + 자동 개선 결과)
    notify_parts = []
    if attention:
        notify_parts.append("수정율 높은 프롬프트:")
        for a in attention[:5]:
            notify_parts.append(f"- {a['prompt_id']}: {a['avg_edit_ratio']*100:.1f}% ({a['edit_count']}건)")
    if results["auto_improvements"]:
        notify_parts.append("\n자동 개선 시작:")
        for imp in results["auto_improvements"]:
            notify_parts.append(f"- {imp['prompt_id']} v{imp['candidate_version']}: {imp['reason']}")

    if notify_parts:
        try:
            from app.services.core.notification_service import send_teams_notification
            await send_teams_notification(
                title="프롬프트 진화 시스템 리포트",
                message="\n".join(notify_parts),
                color="warning" if not results["auto_improvements"] else "good",
            )
        except Exception:
            pass

    logger.info(
        f"프롬프트 유지보수 완료: MV={'OK' if results['mv_refreshed'] else 'SKIP'}, "
        f"주의={len(attention)}건, 실험={len(results['experiments_evaluated'])}건, "
        f"자동개선={len(results['auto_improvements'])}건"
    )
    return results
