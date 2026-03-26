"""
G2B 정기 모니터링 스케줄러 (§25-2)

평일 업무시간(08~18시) 1시간마다 각 팀의 monitor_keywords로 나라장터 공고를 검색,
신규 공고 발견 시 Teams + 인앱 알림.
"""

import asyncio
import logging
from datetime import datetime, timezone

from app.config import settings
from app.utils.supabase_client import get_async_client

logger = logging.getLogger(__name__)


def _is_korean_holiday(dt: datetime) -> bool:
    """한국 공휴일 여부 (주요 법정 공휴일만 체크)."""
    md = (dt.month, dt.day)
    fixed_holidays = {
        (1, 1), (3, 1), (5, 5), (6, 6), (8, 15), (10, 3), (10, 9), (12, 25),
    }
    if md in fixed_holidays:
        return True
    # 음력 공휴일(설날, 추석)은 매년 변동 → 환경 변수 또는 외부 API로 확장 가능
    # 현재는 고정 공휴일만 체크
    return False


async def daily_g2b_monitor() -> dict:
    """일일 G2B 공고 모니터링 (v2: 전수 수집 + 적합도 스코어링).

    평일 08~18시 매시 정각에 스케줄러가 호출. 공휴일이면 스킵.

    Returns:
        {"teams_checked": int, "new_bids_found": int, "notifications_sent": int,
         "total_fetched": int, "scored_passed": int}
    """
    # 공휴일 체크 (KST 기준)
    from zoneinfo import ZoneInfo
    now_kst = datetime.now(ZoneInfo("Asia/Seoul"))
    if _is_korean_holiday(now_kst):
        logger.info(f"공휴일 — G2B 모니터링 스킵 ({now_kst.strftime('%m/%d')})")
        return {"teams_checked": 0, "new_bids_found": 0, "notifications_sent": 0,
                "total_fetched": 0, "scored_passed": 0, "skipped": "holiday"}

    from app.services.bid_scorer import score_and_rank_bids
    from app.services.g2b_service import G2BService
    from app.services.notification_service import (
        _get_user_email_info,
        _should_send_email,
        create_notification,
        send_teams_notification,
    )
    from app.services.email_service import build_email_html, send_email

    client = await get_async_client()
    stats = {
        "teams_checked": 0, "new_bids_found": 0, "notifications_sent": 0,
        "total_fetched": 0, "scored_passed": 0,
    }

    # 활성 팀 조회
    try:
        teams_result = (
            await client.table("teams")
            .select("id, name, monitor_keywords, teams_webhook_url")
            .execute()
        )
        teams = teams_result.data or []
    except Exception as e:
        logger.error(f"팀 목록 조회 실패: {e}")
        return stats

    if not teams:
        return stats

    async with G2BService() as g2b:
        # ── 1) 당일 전체 공고 1회 수집 (팀 공통) ──────────
        today = datetime.now(timezone.utc)
        date_from = today.strftime("%Y%m%d") + "0000"
        date_to = today.strftime("%Y%m%d") + "2359"

        try:
            all_raw = await g2b.fetch_all_bids(date_from, date_to)
        except Exception as e:
            logger.error(f"전수 수집 실패: {e}")
            return stats

        stats["total_fetched"] = len(all_raw)

        # ── 2) 적합도 스코어링 (역할 키워드 + 분류 가중치) ───
        scored = score_and_rank_bids(
            all_raw,
            reference_date=today.date(),
            min_score=0,
            exclude_expired=True,
            max_results=200,
        )
        stats["scored_passed"] = len(scored)

        # scored → bidNtceNm 포함 dict 형태로 변환 (알림용)
        scored_bids = []
        for bs in scored:
            scored_bids.append({
                "bidNtceNo": bs.bid_no,
                "bidNtceNm": bs.title,
                "ntceInsttNm": bs.agency,
                "presmptPrce": str(bs.budget) if bs.budget else "",
                "bidClseDt": bs.deadline,
                "score": bs.score,
                "role_keywords": bs.role_keywords_matched,
            })

        if not scored_bids:
            logger.info("스코어링 통과 공고 없음")
            return stats

        # ── 3) 팀별 알림 ────────────────────────────────
        for team in teams:
            team_id = team["id"]
            stats["teams_checked"] += 1

            try:
                # 이미 알림 보낸 공고 필터링
                new_bids = await _filter_new_bids(client, team_id, scored_bids)
                if not new_bids:
                    continue

                stats["new_bids_found"] += len(new_bids)

                # 알림 발송 (상위 10건 요약)
                bid_summary = _format_scored_bid_summary(new_bids[:10])

                search_link = f"{settings.frontend_url}/bids"

                # Teams 알림
                await send_teams_notification(
                    team_id=team_id,
                    title=f"오늘의 추천 공고 {len(new_bids)}건",
                    body=bid_summary,
                    link=search_link,
                )

                # 팀 리더에게 인앱 알림
                leader = await _get_team_leader(client, team_id)
                if leader:
                    await create_notification(
                        user_id=leader,
                        proposal_id=None,
                        type="g2b_monitor",
                        title=f"오늘의 추천 공고 {len(new_bids)}건",
                        body=bid_summary[:200],
                        link=search_link,
                    )

                # 이메일 (옵트인 팀원에게)
                try:
                    team_members_res = await (
                        client.table("team_members")
                        .select("user_id")
                        .eq("team_id", team_id)
                        .execute()
                    )
                    for member in (team_members_res.data or []):
                        user_data = await _get_user_email_info(member["user_id"])
                        if _should_send_email(user_data, "email_monitoring"):
                            html = build_email_html(
                                title=f"신규 공고 {len(new_bids)}건 발견",
                                body=bid_summary[:500],
                                link=search_link,
                            )
                            await send_email(
                                user_data["email"],
                                f"신규 공고 {len(new_bids)}건",
                                html,
                            )
                except Exception as email_err:
                    logger.debug(f"신규 공고 이메일 발송 실패 (무시): {email_err}")

                # 알림 기록 저장 (중복 방지)
                await _record_notified_bids(client, team_id, new_bids)
                stats["notifications_sent"] += 1

            except Exception as e:
                logger.warning(f"G2B 모니터링 실패 (team={team_id}): {e}")

    logger.info(
        f"G2B 모니터링 완료: 전수 {stats['total_fetched']}건 → "
        f"스코어 {stats['scored_passed']}건 → "
        f"{stats['new_bids_found']}건 신규, {stats['notifications_sent']}건 알림"
    )

    # 백그라운드 파이프라인: score >= 70(추천 이상) → 첨부파일 + AI 분석
    pipeline_targets = [
        b.bid_no for b in scored if b.score >= 70
    ]
    if pipeline_targets:
        try:
            from app.services.bid_pipeline import run_pipeline
            asyncio.create_task(run_pipeline(pipeline_targets))
            logger.info(f"[Monitor] 파이프라인 큐: {len(pipeline_targets)}건")
        except Exception as e:
            logger.warning(f"[Monitor] 파이프라인 시작 실패: {e}")

    return stats


async def _filter_new_bids(
    client: any, team_id: str, bids: list[dict]
) -> list[dict]:
    """이미 알림한 공고 제외."""
    if not bids:
        return []

    bid_nos = [b.get("bidNtceNo", "") for b in bids if b]
    bid_nos = [n for n in bid_nos if n]
    if not bid_nos:
        return bids

    try:
        existing = (
            await client.table("g2b_monitor_log")
            .select("bid_notice_no")
            .eq("team_id", team_id)
            .in_("bid_notice_no", bid_nos)
            .execute()
        )
        notified = {r["bid_notice_no"] for r in (existing.data or [])}
    except Exception:
        # 테이블 미존재 시 전체 반환
        return bids

    return [
        b
        for b in bids
        if b.get("bidNtceNo", "") not in notified
    ]


async def _record_notified_bids(
    client: any, team_id: str, bids: list[dict]
) -> None:
    """알림 발송한 공고 기록 (중복 방지)."""
    rows = []
    now = datetime.now(timezone.utc).isoformat()
    for b in bids:
        bid_no = b.get("bidNtceNo", "")
        if bid_no:
            rows.append({
                "team_id": team_id,
                "bid_notice_no": bid_no,
                "title": b.get("bidNtceNm", "")[:200],
                "notified_at": now,
            })
    if rows:
        try:
            await client.table("g2b_monitor_log").insert(rows).execute()
        except Exception as e:
            logger.debug(f"모니터링 로그 저장 실패 (무시): {e}")


async def _get_team_leader(client: any, team_id: str) -> str | None:
    """팀 리더 user_id 조회."""
    try:
        result = (
            await client.table("users")
            .select("id")
            .eq("team_id", team_id)
            .eq("role", "lead")
            .limit(1)
            .maybe_single()
            .execute()
        )
        return result.data["id"] if result.data else None
    except Exception:
        return None


def _format_bid_summary(bids: list[dict], keyword: str) -> str:
    """공고 요약 텍스트 생성 (v1 레거시 호환)."""
    lines = [f"키워드 '{keyword}'에 매칭된 신규 공고:"]
    for i, b in enumerate(bids, 1):
        title = b.get("bidNtceNm", "제목 없음")
        agency = b.get("ntceInsttNm", b.get("dminsttNm", ""))
        budget_raw = b.get("presmptPrce", b.get("asignBdgtAmt", ""))
        try:
            budget_val = int(str(budget_raw).replace(",", "").strip() or "0")
            budget_str = f"{budget_val:,}원" if budget_val > 0 else "미정"
        except (ValueError, TypeError):
            budget_str = "미정"
        lines.append(f"{i}. {title} ({agency}, {budget_str})")
    return "\n".join(lines)


def _format_scored_bid_summary(bids: list[dict]) -> str:
    """스코어링 기반 공고 요약 텍스트 생성 (v2)."""
    lines = ["적합도 스코어링 기반 추천 공고:"]
    for i, b in enumerate(bids, 1):
        title = b.get("bidNtceNm", "제목 없음")
        agency = b.get("ntceInsttNm", "")
        budget_raw = b.get("presmptPrce", "0")
        try:
            budget_val = int(str(budget_raw).replace(",", "").strip() or "0")
            if budget_val >= 100_000_000:
                budget_str = f"{budget_val / 100_000_000:.1f}억"
            elif budget_val > 0:
                budget_str = f"{budget_val / 10_000:.0f}만"
            else:
                budget_str = "미정"
        except (ValueError, TypeError):
            budget_str = "미정"
        score = b.get("score", 0)
        kws = ", ".join(b.get("role_keywords", []))
        lines.append(f"{i}. [{score:.0f}점] {title} ({agency}, {budget_str}) [{kws}]")
    return "\n".join(lines)


async def send_daily_summary_email() -> int:
    """일일 공고 요약 이메일 — email_daily_summary 옵트인 사용자 대상.

    평일 09:00 KST에 스케줄러가 호출.
    """
    if not settings.email_enabled:
        return 0

    try:
        client = await get_async_client()

        # 옵트인 사용자 조회
        users_res = await (
            client.table("users")
            .select("id, email, name, notification_settings")
            .eq("status", "active")
            .execute()
        )
        recipients = [
            u for u in (users_res.data or [])
            if u.get("email")
            and (u.get("notification_settings") or {}).get("email_monitoring", False)
        ]
        if not recipients:
            logger.debug("일일 요약 이메일 수신자 없음")
            return 0

        # 통계 집계
        from datetime import timedelta
        now = datetime.now(timezone.utc)
        yesterday = (now - timedelta(days=1)).isoformat()

        new_bids_res = await (
            client.table("g2b_bids")
            .select("id", count="exact")
            .gte("fetched_at", yesterday)
            .limit(0)
            .execute()
        )
        recommended_res = await (
            client.table("g2b_bids")
            .select("id", count="exact")
            .gte("fetched_at", yesterday)
            .gte("relevance_score", 70)
            .limit(0)
            .execute()
        )
        urgent_res = await (
            client.table("g2b_bids")
            .select("id", count="exact")
            .gte("deadline", now.isoformat())
            .lte("deadline", (now + timedelta(days=3)).isoformat())
            .eq("status", "active")
            .limit(0)
            .execute()
        )
        active_res = await (
            client.table("proposals")
            .select("id", count="exact")
            .not_.in_("status", ["won", "lost", "cancelled", "expired"])
            .limit(0)
            .execute()
        )

        new_bids = new_bids_res.count or 0
        recommended = recommended_res.count or 0
        urgent = urgent_res.count or 0
        active_proposals = active_res.count or 0

        from app.services.email_service import build_email_html, send_email_batch
        body = (
            f"신규 공고: <b>{new_bids}</b>건<br>"
            f"AI 추천: <b>{recommended}</b>건 (70점 이상)<br>"
            f"마감 임박 (D-3 이내): <b>{urgent}</b>건<br>"
            f"진행중 제안서: <b>{active_proposals}</b>건"
        )
        html = build_email_html(
            title="일일 공고 현황 요약",
            body=body,
            link=f"{settings.frontend_url}/monitoring",
        )

        sent = await send_email_batch(
            [u["email"] for u in recipients],
            "일일 공고 현황 요약",
            html,
        )
        logger.info(f"일일 요약 이메일 발송: {sent}/{len(recipients)}명")
        return sent
    except Exception as e:
        logger.warning(f"일일 요약 이메일 실패: {e}")
        return 0


def setup_scheduler() -> None:
    """APScheduler 기반 스케줄러 설정.

    main.py lifespan에서 호출. APScheduler 미설치 시 graceful skip.
    """
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from apscheduler.triggers.cron import CronTrigger
        from zoneinfo import ZoneInfo

        kst = ZoneInfo("Asia/Seoul")
        scheduler = AsyncIOScheduler(timezone=kst)
        # 평일(월~금) 업무시간(08~18시) 1시간마다 실행
        scheduler.add_job(
            daily_g2b_monitor,
            trigger=CronTrigger(
                hour="8-18", minute=0, day_of_week="mon-fri", timezone=kst,
            ),
            id="g2b_monitor_hourly",
            name="G2B 1시간 주기 모니터링 (평일 08~18시)",
            replace_existing=True,
        )
        # 프롬프트 진화 유지보수 (매일 02:00 KST — MV 갱신 + 주의 프롬프트 감지 + A/B 자동 평가)
        from app.services.prompt_tracker import periodic_maintenance
        scheduler.add_job(
            periodic_maintenance,
            trigger=CronTrigger(hour=2, minute=0, timezone=kst),
            id="prompt_evolution_maintenance",
            name="프롬프트 진화 유지보수",
            replace_existing=True,
        )

        # 일일 요약 이메일 (평일 09:00 KST)
        scheduler.add_job(
            send_daily_summary_email,
            trigger=CronTrigger(hour=9, minute=0, day_of_week="mon-fri", timezone=kst),
            id="daily_summary_email",
            name="일일 요약 이메일 (평일 09:00)",
            replace_existing=True,
        )

        # ── 자가검증 잡 ──
        if settings.health_check_enabled:
            from app.services.health_checker import HealthCheckRunner
            from app.services.alert_manager import AlertManager

            _hc_runner = HealthCheckRunner()
            _hc_alerter = AlertManager()

            async def _health_run(category: str):
                results = await _hc_runner.run_category(category)
                await _hc_alerter.handle_results(results)

            async def _health_run_external_and_api():
                r1 = await _hc_runner.run_category("external")
                r2 = await _hc_runner.run_category("api")
                await _hc_alerter.handle_results(r1 + r2)

            # 인프라: 매 5분
            scheduler.add_job(
                lambda: asyncio.ensure_future(_health_run("infra")),
                trigger=CronTrigger(minute="*/5", timezone=kst),
                id="health_infra",
                name="자가검증: 인프라 (5분)",
                replace_existing=True,
            )
            # 데이터 정합성: 매 30분 (05분, 35분)
            scheduler.add_job(
                lambda: asyncio.ensure_future(_health_run("data")),
                trigger=CronTrigger(minute="5,35", timezone=kst),
                id="health_data",
                name="자가검증: 데이터 정합성 (30분)",
                replace_existing=True,
            )
            # 외부+API 스모크: 매 1시간 (15분)
            scheduler.add_job(
                lambda: asyncio.ensure_future(_health_run_external_and_api()),
                trigger=CronTrigger(minute=15, timezone=kst),
                id="health_external_api",
                name="자가검증: 외부 서비스+API (1시간)",
                replace_existing=True,
            )
            logger.info("자가검증 스케줄러 등록 완료 (인프라 5분, 데이터 30분, 외부+API 1시간)")

        scheduler.start()
        logger.info("스케줄러 시작: G2B 모니터링 + 일일 요약 + 프롬프트 유지보수 + 자가검증")
    except ImportError:
        logger.info("APScheduler 미설치 — 스케줄러 비활성화")
    except Exception as e:
        logger.warning(f"스케줄러 설정 실패: {e}")
