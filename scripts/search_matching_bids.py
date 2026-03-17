"""
테크노베이션파트너스 역량 기반 맞춤형 G2B 공고 검색

data/company_profile.json을 로드하여 G2B 공고를 검색하고
키워드 매칭으로 적합도 스코어를 계산한다.

사용법:
    uv run python scripts/search_matching_bids.py                    # 기본 검색
    uv run python scripts/search_matching_bids.py --min-score 70     # 70점 이상만
    uv run python scripts/search_matching_bids.py --min-budget 50000 # 5천만원 이상
    uv run python scripts/search_matching_bids.py --days 21          # 최근 21일
    uv run python scripts/search_matching_bids.py --show-excluded    # 마감임박 포함 출력
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.services.g2b_service import G2BService

PROFILE_PATH = PROJECT_ROOT / "data" / "company_profile.json"

# 마감 최소 잔여일
MIN_DAYS_BEFORE_DEADLINE = 3

# 용역 유형 필터 (물품/공사 제외)
SERVICE_TYPES = {"일반용역", "기술용역", "학술용역", ""}


def load_profile() -> dict:
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


def days_until_deadline(deadline_str: str) -> int | None:
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


def _build_client_to_dept(profile: dict) -> dict[str, str]:
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
    # bidClseDt가 비어있는 경우 opengDt(개찰일시) 사용
    deadline = bid.get("bidClseDt") or bid.get("opengDt") or bid.get("rbidOpengDt") or ""
    bid_type = bid.get("srvceDivNm", "")
    bid_category = bid.get("pubPrcrmntLrgClsfcNm", "")

    ki = profile["keyword_index"]
    search_kw = profile["search_keywords"]
    stats = profile["company"]["stats"]

    # ── 1. 도메인 키워드 (40점) ──
    # 키워드 빈도 가중: 고빈도 키워드 매칭에 더 높은 점수
    title_lower = title.lower()
    domain_kw = ki.get("domain_keywords", {})
    matched_kw = []
    weighted_hits = 0.0
    for kw in search_kw:
        if kw.lower() in title_lower:
            matched_kw.append(kw)
            freq = domain_kw.get(kw, 1)
            # 빈도 높을수록 가중치 (log scale)
            import math
            weighted_hits += 1.0 + math.log2(max(freq, 1)) * 0.15

    # 2.0 가중히트 이상이면 만점
    kw_score = min(weighted_hits / 2.0, 1.0) * 40

    # ── 2. 발주처 매칭 (30점) ──
    client_freq = ki.get("client_frequency", {})
    if client in client_freq:
        # 기존 고객: 실적 많을수록 높은 점수 (최소 20, 최대 30)
        freq = client_freq[client]
        client_score = min(20.0 + freq * 0.5, 30.0)
    else:
        # 부분 매칭: 발주처명 핵심 부분 비교 (예: "한국보건산업진흥원" ∈ "한국보건산업진흥원 부산지부")
        partial_match = None
        for known_client in client_freq:
            if known_client in client or client in known_client:
                partial_match = known_client
                break
        if partial_match:
            client_score = 15.0
        else:
            client_score = 0.0

    # ── 3. 부처 경험 (20점) ──
    dept_freq = ki.get("department_frequency", {})
    total_projects = stats["total_projects"] or 1

    # 발주처→부처 매핑으로 부처 추정
    dept_score = 0.0
    matched_dept = None
    # 먼저 기존 매핑에서 찾기
    for known_client, dept in client_dept_map.items():
        if known_client in client or client in known_client:
            count = dept_freq.get(dept, 0)
            if count > 0:
                matched_dept = dept
                dept_score = min((count / total_projects) * 100, 20.0)
                break
    # 매핑 없으면 제목+발주처에서 부처 키워드 탐색
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
        # tenopa 적합 범위: 1천만원 ~ 7억원
        if 10_000_000 <= budget <= 700_000_000:
            budget_score = 10.0
        elif budget < 10_000_000:
            budget_score = 3.0  # 소규모
        else:
            budget_score = 5.0  # 대규모 (컨소시엄 가능)

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


async def search_and_score(
    profile: dict,
    min_score: int = 50,
    min_budget: int = 0,
    date_range_days: int = 14,
) -> list[dict]:
    """G2B 전체 조회 → 용역 필터 → 스코어링 → 정렬."""
    async with G2BService() as svc:
        print(f"G2B 공고 검색 중 (최근 {date_range_days}일, 최대 999건)...")
        raw_bids = await svc.search_bid_announcements(
            keyword="",  # 전체 조회
            num_of_rows=999,
            date_from=(datetime.now() - timedelta(days=date_range_days)).strftime("%Y%m%d") + "0000",
        )
        print(f"  → {len(raw_bids)}건 조회됨")

    # 용역 유형 필터 (물품/공사 제외)
    service_bids = [
        b for b in raw_bids
        if b.get("srvceDivNm", "") in SERVICE_TYPES
    ]
    if len(service_bids) < len(raw_bids):
        print(f"  → 용역 필터 후 {len(service_bids)}건 (물품/공사 {len(raw_bids) - len(service_bids)}건 제외)")

    client_dept_map = _build_client_to_dept(profile)

    scored = []
    for bid in service_bids:
        result = score_bid(bid, profile, client_dept_map)
        if result["score"] >= min_score and result["budget"] >= min_budget:
            scored.append(result)

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored


def format_budget(amount: int) -> str:
    """예산 한국식 표기."""
    if amount >= 100_000_000:
        return f"{amount / 100_000_000:.1f}억"
    elif amount >= 10_000:
        return f"{amount / 10_000:,.0f}만원"
    return f"{amount:,}원"


def format_d_day(d_days: int | None) -> str:
    """D-day 표시 포맷."""
    if d_days is None:
        return "마감일 미상"
    if d_days < 0:
        return f"마감({-d_days}일 전)"
    if d_days == 0:
        return "오늘 마감"
    return f"D-{d_days}"


def print_results(scored: list[dict], show_excluded: bool = False):
    """결과 출력."""
    now = datetime.now().strftime("%Y-%m-%d")
    print(f"\n━━━ 테크노베이션파트너스 맞춤 공고 검색 ({now}) ━━━\n")

    active = [s for s in scored if not s["excluded"]]
    excluded = [s for s in scored if s["excluded"]]

    if not active and not excluded:
        print("  매칭되는 공고가 없습니다.")
        return

    for s in active:
        d_str = format_d_day(s["d_days"])
        print(f"[{s['score']}점] {s['title']}")
        print(f"   발주: {s['client']}  예산: {format_budget(s['budget'])}  마감: {d_str}")

        detail = s["score_detail"]
        parts = []
        if s["matched_keywords"]:
            parts.append(f"키워드({','.join(s['matched_keywords'][:4])})")
        if detail["client"] > 0:
            parts.append(f"{'기존고객' if detail['client'] >= 20 else '유사고객'}({detail['client']:.0f}점)")
        if s["matched_dept"]:
            parts.append(f"부처경험:{s['matched_dept']}({detail['department']:.0f}점)")
        if parts:
            print(f"   매칭: {' + '.join(parts)}")
        print()

    if excluded:
        print(f"─── 마감 D-{MIN_DAYS_BEFORE_DEADLINE} 미만 제외 ({len(excluded)}건) ───\n")
        show_count = len(excluded) if show_excluded else min(5, len(excluded))
        for s in excluded[:show_count]:
            d_str = format_d_day(s["d_days"])
            kw_str = f"  [{','.join(s['matched_keywords'][:3])}]" if s["matched_keywords"] else ""
            print(f"  [{s['score']}점] {s['title']}  ({d_str}){kw_str}")
        if not show_excluded and len(excluded) > 5:
            print(f"  ... 외 {len(excluded) - 5}건 (--show-excluded 로 전체 보기)")

    print(f"\n총 {len(active)}건 추천 / {len(excluded)}건 마감임박 제외")


def main():
    parser = argparse.ArgumentParser(description="테크노베이션파트너스 맞춤 G2B 공고 검색")
    parser.add_argument("--min-score", type=int, default=50, help="최소 적합도 (기본: 50)")
    parser.add_argument("--min-budget", type=int, default=0, help="최소 예산 (천원 단위, 기본: 0)")
    parser.add_argument("--days", type=int, default=14, help="검색 기간 일수 (기본: 14)")
    parser.add_argument("--show-excluded", action="store_true", help="마감임박 제외 공고 전체 표시")
    args = parser.parse_args()

    if not PROFILE_PATH.exists():
        print(f"[ERROR] 역량 프로필 없음: {PROFILE_PATH}")
        print("먼저 import_project_history.py를 실행하세요.")
        sys.exit(1)

    profile = load_profile()
    print(f"역량 프로필 로드: {profile['company']['stats']['total_projects']}건 실적, "
          f"{len(profile['search_keywords'])}개 키워드")

    scored = asyncio.run(search_and_score(
        profile,
        min_score=args.min_score,
        min_budget=args.min_budget * 1000,  # 천원 → 원
        date_range_days=args.days,
    ))

    print_results(scored, show_excluded=args.show_excluded)


if __name__ == "__main__":
    main()
