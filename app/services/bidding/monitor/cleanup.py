"""
공고 자동 정리 서비스

서버 시작 시 실행:
1. days_remaining 갱신 (수집 시점 → 오늘 기준)
2. 마감 30일 경과 + 제안결정 안 한 건 삭제
3. 관련없음 확정 후 7일 경과 건 삭제
4. 캐시 파일 동기화 (삭제된 공고의 캐시도 삭제)
"""

import json
import logging
from datetime import date, datetime, timezone
from pathlib import Path

from app.utils.supabase_client import get_async_client

logger = logging.getLogger(__name__)


async def cleanup_expired_bids() -> dict:
    """공고 자동 정리. 서버 시작 시 호출."""
    client = await get_async_client()
    today = date.today()
    result = {"updated": 0, "deleted": 0, "cache_cleaned": 0}

    # 1. days_remaining 갱신 (deadline_date 기준으로 재계산)
    try:
        all_bids = (
            await client.table("bid_announcements")
            .select("bid_no, deadline_date")
            .execute()
        )
        for bid in (all_bids.data or []):
            if not bid.get("deadline_date"):
                continue
            deadline = datetime.fromisoformat(bid["deadline_date"].replace("Z", "+00:00"))
            new_days = (deadline.date() - today).days
            await (
                client.table("bid_announcements")
                .update({"days_remaining": new_days})
                .eq("bid_no", bid["bid_no"])
                .execute()
            )
            result["updated"] += 1
    except Exception as e:
        logger.warning(f"days_remaining 갱신 실패: {e}")

    # 2. 마감 30일 경과 + 제안결정 안 한 건 삭제
    status_dir = Path("data/bid_status")
    decided_bids = set()
    if status_dir.exists():
        for f in status_dir.glob("*.json"):
            try:
                st = json.loads(f.read_text(encoding="utf-8"))
                if st.get("status") in ("제안결정", "제안착수"):
                    decided_bids.add(st.get("bid_no", f.stem))
            except Exception:
                pass

    try:
        expired = (
            await client.table("bid_announcements")
            .select("bid_no")
            .lt("days_remaining", -30)
            .execute()
        )
        for bid in (expired.data or []):
            bid_no = bid["bid_no"]
            if bid_no in decided_bids:
                continue  # 제안결정 건은 보관
            try:
                await (
                    client.table("bid_announcements")
                    .delete()
                    .eq("bid_no", bid_no)
                    .execute()
                )
                _clean_cache(bid_no)
                result["deleted"] += 1
            except Exception:
                pass
    except Exception as e:
        logger.warning(f"마감 경과 공고 삭제 실패: {e}")

    # 3. 관련없음 확정 후 7일 경과 건 삭제
    if status_dir.exists():
        for f in status_dir.glob("*.json"):
            try:
                st = json.loads(f.read_text(encoding="utf-8"))
                if st.get("status") != "관련없음":
                    continue
                # 파일 수정일 기준 7일 경과 확인
                mtime = datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc)
                days_since = (datetime.now(timezone.utc) - mtime).days
                if days_since < 7:
                    continue
                bid_no = f.stem
                try:
                    await (
                        client.table("bid_announcements")
                        .delete()
                        .eq("bid_no", bid_no)
                        .execute()
                    )
                except Exception:
                    pass
                _clean_cache(bid_no)
                result["deleted"] += 1
            except Exception:
                pass

    return result


def _clean_cache(bid_no: str):
    """공고 관련 캐시 파일 삭제."""
    for cache_dir in ["data/bid_analyses", "data/bid_status"]:
        cache_file = Path(cache_dir) / f"{bid_no}.json"
        if cache_file.exists():
            try:
                cache_file.unlink()
            except Exception:
                pass
