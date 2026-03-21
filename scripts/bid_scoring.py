"""
공통 스코어링 + 키워드 검색 모듈

search_matching_bids.py와 daily_bid_scan.py에서 공유.
"""

import json
import math
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROFILE_PATH = PROJECT_ROOT / "data" / "company_profile.json"

# 마감 최소 잔여일
MIN_DAYS_BEFORE_DEADLINE = 3

# 용역 유형 필터 (물품/공사 제외)
SERVICE_TYPES = {"일반용역", "기술용역", "학술용역", ""}


def load_profile() -> dict:
    """data/company_profile.json 로드."""
    with open(PROFILE_PATH, encoding="utf-8") as f:
        return json.load(f)


def parse_budget(raw) -> int:
    """공고 예산 문자열 → 원 단위 정수."""
    if not raw:
        return 0
    try:
        return int(str(raw).replace(",", "").strip() or "0")
    except (ValueError, TypeError):
        return 0


def days_until_deadline(deadline_str: str) -> Optional[int]:
    """마감일까지 남은 일수. 파싱 실패 시 None."""
    if not deadline_str:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S", "%Y%m%d%H%M", "%Y%m%d"):
        try:
            dt = datetime.strptime(deadline_str.strip()[:19], fmt)
            return (dt - datetime.now()).days
        except ValueError:
            continue
    return None


def build_client_to_dept(profile: dict) -> dict[str, str]:
    """track_records에서 발주처→부처 매핑 구축."""
    mapping: dict[str, str] = {}
    for r in profile["track_records"]:
        if r["client"] and r["department"]:
            mapping[r["client"]] = r["department"]
    return mapping


def score_bid(bid: dict, profile: dict, client_dept_map: dict[str, str]) -> dict:
    """
    공고에 대한 적합도 스코어 (0~100) 계산.

    배점:
    - 도메인 키워드 매칭: 40점
    - 발주처 기존고객: 30점
    - 부처 경험: 20점
    - 예산 범위 적합: 10점
    """
    title = bid.get("bidNtceNm", "")
    client = bid.get("ntceInsttNm", "") or bid.get("dminsttNm", "")
    budget = parse_budget(bid.get("presmptPrce") or bid.get("asignBdgtAmt"))
    deadline = bid.get("bidClseDt") or bid.get("opengDt") or bid.get("rbidOpengDt") or ""
    bid_type = bid.get("srvceDivNm", "")
    bid_category = bid.get("pubPrcrmntLrgClsfcNm", "")

    ki = profile["keyword_index"]
    search_kw = profile["search_keywords"]
    stats = profile["company"]["stats"]

    # ── 1. 도메인 키워드 (40점) ──
    title_lower = title.lower()
    domain_kw = ki.get("domain_keywords", {})
    matched_kw = []
    weighted_hits = 0.0
    for kw in search_kw:
        if kw.lower() in title_lower:
            matched_kw.append(kw)
            freq = domain_kw.get(kw, 1)
            weighted_hits += 1.0 + math.log2(max(freq, 1)) * 0.15

    kw_score = min(weighted_hits / 2.0, 1.0) * 40

    # ── 2. 발주처 매칭 (30점) ──
    client_freq = ki.get("client_frequency", {})
    if client in client_freq:
        freq = client_freq[client]
        client_score = min(20.0 + freq * 0.5, 30.0)
    else:
        partial_match = None
        for known_client in client_freq:
            if known_client in client or client in known_client:
                partial_match = known_client
                break
        client_score = 15.0 if partial_match else 0.0

    # ── 3. 부처 경험 (20점) ──
    dept_freq = ki.get("department_frequency", {})
    total_projects = stats["total_projects"] or 1

    dept_score = 0.0
    matched_dept = None
    for known_client, dept in client_dept_map.items():
        if known_client in client or client in known_client:
            count = dept_freq.get(dept, 0)
            if count > 0:
                matched_dept = dept
                dept_score = min((count / total_projects) * 100, 20.0)
                break
    if not matched_dept:
        text = title + " " + client
        for dept, count in dept_freq.items():
            if dept in text:
                matched_dept = dept
                dept_score = min((count / total_projects) * 100, 20.0)
                break

    # ── 4. 예산 범위 (10점) ──
    budget_score = 0.0
    if budget > 0:
        if 10_000_000 <= budget <= 700_000_000:
            budget_score = 10.0
        elif budget < 10_000_000:
            budget_score = 3.0
        else:
            budget_score = 5.0

    total_score = round(kw_score + client_score + dept_score + budget_score)
    d_days = days_until_deadline(deadline)

    return {
        "score": total_score,
        "title": title,
        "client": client,
        "budget": budget,
        "deadline": deadline,
        "d_days": d_days,
        "bid_no": bid.get("bidNtceNo", ""),
        "url": bid.get("bidNtceDtlUrl", ""),
        "bid_type": bid_type,
        "bid_category": bid_category,
        "matched_keywords": matched_kw,
        "matched_dept": matched_dept,
        "score_detail": {
            "keyword": round(kw_score, 1),
            "client": round(client_score, 1),
            "department": round(dept_score, 1),
            "budget": round(budget_score, 1),
        },
        "excluded": d_days is not None and d_days < MIN_DAYS_BEFORE_DEADLINE,
    }


def format_budget(amount: int) -> str:
    """예산 한국식 표기."""
    if amount >= 100_000_000:
        return f"{amount / 100_000_000:.1f}억"
    elif amount >= 10_000:
        return f"{amount / 10_000:,.0f}만원"
    return f"{amount:,}원"


def format_d_day(d_days: Optional[int]) -> str:
    """D-day 표시 포맷."""
    if d_days is None:
        return "마감일 미상"
    if d_days < 0:
        return f"마감({-d_days}일 전)"
    if d_days == 0:
        return "오늘 마감"
    return f"D-{d_days}"


async def search_by_keywords(svc, keywords: list[str], num_per_kw: int = 100,
                              date_from: Optional[str] = None,
                              date_to: Optional[str] = None) -> dict[str, dict]:
    """
    키워드별 개별 API 호출 → 합산 + 중복 제거.

    Returns:
        {bid_no: raw_bid_dict} (matched_keywords 필드 첨부)
    """
    all_bids: dict[str, dict] = {}
    for kw in keywords:
        results = await svc.search_bid_announcements(
            keyword=kw,
            num_of_rows=num_per_kw,
            date_from=date_from,
            date_to=date_to,
        )
        for bid in results:
            bid_no = bid.get("bidNtceNo", "")
            if not bid_no:
                continue
            if bid_no not in all_bids:
                all_bids[bid_no] = {**bid, "matched_keywords": [kw]}
            else:
                existing_kws = all_bids[bid_no].get("matched_keywords", [])
                if kw not in existing_kws:
                    existing_kws.append(kw)
    return all_bids
