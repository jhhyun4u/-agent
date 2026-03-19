"""
G2B 정기 모니터링 스케줄러 (§25-2)

매일 08:00, 15:00 2회 각 팀의 monitor_keywords로 나라장터 공고를 검색,
신규 공고 발견 시 Teams + 인앱 알림.
"""

import asyncio
import logging
from datetime import datetime, timezone

from app.config import settings
from app.utils.supabase_client import get_async_client

logger = logging.getLogger(__name__)


async def daily_g2b_monitor() -> dict:
    """일일 G2B 공고 모니터링 (SRC-11).

    Returns:
        {"teams_checked": int, "new_bids_found": int, "notifications_sent": int}
    """
    from app.services.g2b_service import G2BService
    from app.services.notification_service import (
        create_notification,
        send_teams_notification,
    )

    client = await get_async_client()
    stats = {"teams_checked": 0, "new_bids_found": 0, "notifications_sent": 0}

    # 활성 팀 + 모니터링 키워드 조회
    try:
        teams_result = (
            await client.table("teams")
            .select("id, name, monitor_keywords, teams_webhook_url")
            .not_.is_("monitor_keywords", "null")
            .execute()
        )
        teams = teams_result.data or []
    except Exception as e:
        logger.error(f"팀 목록 조회 실패: {e}")
        return stats

    async with G2BService() as g2b:
        for team in teams:
            team_id = team["id"]
            keywords = team.get("monitor_keywords", [])
            if not keywords:
                continue

            stats["teams_checked"] += 1

            for keyword in keywords:
                try:
                    # G2B 본공고 검색
                    results = await g2b.search_bid_announcements(keyword, num_of_rows=50)

                    # 사전규격도 검색하여 합산
                    try:
                        pre_results = await g2b.search_pre_bid_specifications(keyword, num_of_rows=50)
                        # 사전규격 결과를 본공고 형식에 맞춰 변환
                        for pr in pre_results:
                            pr["bidNtceNo"] = f"PRE-{pr.get('prcSpcfNo', '')}"
                            pr["bidNtceNm"] = f"[사전규격] {pr.get('prcSpcfNm', '')}"
                            pr["ntceInsttNm"] = pr.get("orderInsttNm") or pr.get("rlDminsttNm", "")
                            pr["dminsttNm"] = pr.get("orderInsttNm", "")
                            pr["presmptPrce"] = pr.get("asignBdgtAmt") or pr.get("presmptPrce")
                        results.extend(pre_results)
                    except Exception as e:
                        logger.debug(f"사전규격 검색 실패 (무시): {e}")
                    if not results:
                        continue

                    # 이미 알림 보낸 공고 필터링
                    new_bids = await _filter_new_bids(client, team_id, results)
                    if not new_bids:
                        continue

                    stats["new_bids_found"] += len(new_bids)

                    # 알림 발송 (최대 5건 요약)
                    bid_summary = _format_bid_summary(new_bids[:5], keyword)

                    # 알림 링크: APP_URL + /projects?search={keyword} (§25-2)
                    from urllib.parse import quote
                    search_link = (
                        f"{settings.frontend_url}/projects?search={quote(keyword)}"
                    )

                    # Teams 알림
                    await send_teams_notification(
                        team_id=team_id,
                        title=f"신규 공고 알림: '{keyword}' ({len(new_bids)}건)",
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
                            title=f"신규 공고 {len(new_bids)}건 ({keyword})",
                            body=bid_summary[:200],
                            link=search_link,
                        )

                    # 알림 기록 저장 (중복 방지)
                    await _record_notified_bids(client, team_id, new_bids)
                    stats["notifications_sent"] += 1

                    # Rate limit: G2B API 0.1초 간격
                    await asyncio.sleep(0.1)

                except Exception as e:
                    logger.warning(f"G2B 모니터링 실패 (team={team_id}, kw={keyword}): {e}")

    logger.info(
        f"G2B 모니터링 완료: {stats['teams_checked']}팀, "
        f"{stats['new_bids_found']}건 신규, {stats['notifications_sent']}건 알림"
    )
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
    """공고 요약 텍스트 생성."""
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


def setup_scheduler() -> None:
    """APScheduler 기반 스케줄러 설정.

    main.py lifespan에서 호출. APScheduler 미설치 시 graceful skip.
    """
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from apscheduler.triggers.cron import CronTrigger

        scheduler = AsyncIOScheduler()
        scheduler.add_job(
            daily_g2b_monitor,
            trigger=CronTrigger(hour=8, minute=0),
            id="g2b_monitor_morning",
            name="G2B 오전 모니터링",
            replace_existing=True,
        )
        scheduler.add_job(
            daily_g2b_monitor,
            trigger=CronTrigger(hour=15, minute=0),
            id="g2b_monitor_afternoon",
            name="G2B 오후 모니터링",
            replace_existing=True,
        )
        scheduler.start()
        logger.info("G2B 모니터링 스케줄러 시작 (매일 08:00, 15:00)")
    except ImportError:
        logger.info("APScheduler 미설치 — G2B 스케줄러 비활성화")
    except Exception as e:
        logger.warning(f"스케줄러 설정 실패: {e}")
