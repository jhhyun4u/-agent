"""
Utility functions and constants for bid API
"""

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from app.config import settings
from app.exceptions import FileNotFoundError_

logger = logging.getLogger(__name__)

# ── 공고 스코어링 파일 캐시 ──────────────────────────────────
_SCORED_CACHE_FILE = Path("data/bid_scored_cache.json")
_SCORED_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)

_BID_NO_PATTERN = re.compile(r'^[A-Za-z0-9\-]+$')
_FETCH_COOLDOWN_HOURS = 1

_MONITOR_BASE_FIELDS = (
    "bid_no, bid_title, agency, budget_amount, deadline_date, "
    "days_remaining, bid_type, content_text, raw_data, proposal_status"
)


def _load_file_cache() -> dict:
    try:
        if _SCORED_CACHE_FILE.exists():
            return json.loads(_SCORED_CACHE_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def _save_file_cache(cache: dict) -> None:
    try:
        _SCORED_CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    except Exception as e:
        logger.warning(f"파일 캐시 저장 실패: {e}")


def _escape_like(value: str) -> str:
    """PostgREST ilike 메타문자(%, _, \\) 이스케이프"""
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _extract_content_from_raw(raw: dict) -> str:
    """raw_data에서 content_text 추출"""
    if isinstance(raw, dict):
        return raw.get("content_text") or raw.get("body") or ""
    return str(raw) if raw else ""


def _check_analysis_cache(cache_file, bid_no: str) -> dict | None:
    """분석 캐시 확인"""
    try:
        if cache_file.exists():
            data = json.loads(cache_file.read_text(encoding="utf-8"))
            return data.get(bid_no)
    except Exception:
        pass
    return None


async def _load_bid_content(bid_no: str) -> tuple[dict, str]:
    """입찰 공고 내용 로드"""
    from app.utils.supabase_client import get_async_client

    client = await get_async_client()
    res = (
        await client.table("bid_announcements")
        .select("raw_data, content_text")
        .eq("bid_no", bid_no)
        .maybe_single()
        .execute()
    )

    if not res.data:
        raise FileNotFoundError_(f"공고를 찾을 수 없습니다: {bid_no}")

    raw = res.data.get("raw_data") or {}
    content_text = res.data.get("content_text") or _extract_content_from_raw(raw)
    return raw, content_text


def _load_teams_info() -> tuple[str, set[str]]:
    """팀 정보 로드 (company_id, team_ids)"""
    import os
    company_id = os.environ.get("COMPANY_ID", "")
    team_ids = set()
    return company_id, team_ids


def _format_rfp_sections(sections: list[dict]) -> str:
    """RFP 섹션 포매팅"""
    if not sections:
        return ""
    return "\n".join(f"## {s.get('title', 'Section')}\n{s.get('content', '')}" for s in sections)


def _format_notice_markdown(bid: dict, content: str) -> str:
    """공고 마크다운 포매팅"""
    bid_no = bid.get("bid_no", "N/A")
    title = bid.get("bid_title", "No Title")
    agency = bid.get("agency", "N/A")
    deadline = bid.get("deadline_date", "N/A")

    return f"""# {title}

**공고번호**: {bid_no}
**발주기관**: {agency}
**마감일시**: {deadline}

## 공고 내용

{content}
"""
