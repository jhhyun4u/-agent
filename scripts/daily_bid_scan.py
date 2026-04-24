"""
일일 공고 모니터링 + 파이프라인 관리

로컬 JSON(data/bid_pipeline.json) 기반 증분 스캔.
향후 Supabase 연결 시 DB 전환 가능.

사용법:
    uv run python scripts/daily_bid_scan.py              # 일일 증분 스캔
    uv run python scripts/daily_bid_scan.py --init        # 최초 14일 전수 조회
    uv run python scripts/daily_bid_scan.py --select R26BK01363113 --by 홍길동
    uv run python scripts/daily_bid_scan.py --list        # 현재 활성 공고
    uv run python scripts/daily_bid_scan.py --cleanup     # 마감 공고 정리만
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.services.domains.bidding.g2b_service import G2BService
from scripts.bid_scoring import (
    SERVICE_TYPES,
    build_client_to_dept,
    format_budget,
    format_d_day,
    load_profile,
    score_bid,
    search_by_keywords,
)
from scripts.team_recommender import TeamRecommender

PIPELINE_PATH = PROJECT_ROOT / "data" / "bid_pipeline.json"
TEAM_PATH = PROJECT_ROOT / "data" / "team_structure.json"
MAX_KEYWORDS = 25
MIN_SCORE = 50  # active_bids 진입 최소 스코어


# ── 팀 추천 ──────────────────────────────────────

def _get_recommender() -> TeamRecommender | None:
    """팀 추천기 초기화. 팀 데이터 없으면 None."""
    if not TEAM_PATH.exists():
        return None
    try:
        return TeamRecommender()
    except Exception:
        return None


def enrich_with_team(bid: dict, recommender: TeamRecommender | None) -> dict:
    """공고에 추천팀 정보를 첨부."""
    if recommender is None:
        return bid

    title = bid.get("title", "")
    client = bid.get("client", "")
    results, domain = recommender.recommend(title, client, top_n=3)

    # 점수 0인 팀 제외
    recs = [r.to_pipeline_dict() for r in results if r.score > 0]

    bid["recommended_teams"] = recs
    bid["domain"] = domain
    return bid


# ── 파이프라인 JSON I/O ──────────────────────────

def _empty_pipeline() -> dict:
    return {
        "last_scan": None,
        "active_bids": [],
        "archived": [],
        "stats": {
            "total_scanned": 0,
            "total_recommended": 0,
            "total_selected": 0,
            "total_expired": 0,
        },
    }


def load_pipeline() -> dict:
    if PIPELINE_PATH.exists():
        with open(PIPELINE_PATH, encoding="utf-8") as f:
            return json.load(f)
    return _empty_pipeline()


def save_pipeline(data: dict):
    PIPELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(PIPELINE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ── 마감 공고 정리 ──────────────────────────────

def cleanup_expired(pipeline: dict) -> int:
    """deadline 지난 공고를 archived로 이동. 이동 건수 반환."""
    now = datetime.now()
    still_active = []
    moved = 0
    for bid in pipeline["active_bids"]:
        deadline_str = bid.get("deadline", "")
        expired = False
        if deadline_str:
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S", "%Y%m%d%H%M", "%Y%m%d"):
                try:
                    dt = datetime.strptime(deadline_str.strip()[:19], fmt)
                    if dt < now:
                        expired = True
                    break
                except ValueError:
                    continue
        if expired:
            bid["status"] = bid.get("status", "new") if bid.get("status") == "selected" else "expired"
            pipeline["archived"].append(bid)
            pipeline["stats"]["total_expired"] += 1
            moved += 1
        else:
            still_active.append(bid)
    pipeline["active_bids"] = still_active
    return moved


# ── 스캔 ────────────────────────────────────────

async def scan(profile: dict, pipeline: dict, init: bool = False,
               recommender: TeamRecommender | None = None) -> int:
    """키워드별 검색 → 신규만 active_bids에 추가. 추가 건수 반환."""
    keywords = profile["search_keywords"][:MAX_KEYWORDS]
    existing_nos = {b["bid_no"] for b in pipeline["active_bids"]}
    existing_nos |= {b["bid_no"] for b in pipeline["archived"]}

    if init:
        date_range_days = 14
        print(f"[초기화] 최근 {date_range_days}일 전수 조회 시작...")
    else:
        date_range_days = 1
        print("[증분] 전일 24시간 공고 조회 시작...")

    date_from = (datetime.now() - timedelta(days=date_range_days)).strftime("%Y%m%d") + "0000"

    async with G2BService() as svc:
        all_bids = await search_by_keywords(svc, keywords, num_per_kw=100, date_from=date_from)

    print(f"  → {len(all_bids)}건 수집 (중복 제거 후)")

    # 용역 필터
    service_bids = {
        no: b for no, b in all_bids.items()
        if b.get("srvceDivNm", "") in SERVICE_TYPES
    }

    client_dept_map = build_client_to_dept(profile)
    added = 0
    skipped_no_team = 0

    for bid_no, raw_bid in service_bids.items():
        if bid_no in existing_nos:
            continue

        result = score_bid(raw_bid, profile, client_dept_map)
        if result["score"] < MIN_SCORE:
            continue

        entry = {
            "bid_no": result["bid_no"],
            "title": result["title"],
            "client": result["client"],
            "budget": result["budget"],
            "deadline": result["deadline"],
            "url": result["url"],
            "score": result["score"],
            "score_detail": result["score_detail"],
            "matched_keywords": result["matched_keywords"],
            "status": "new",
            "first_seen": datetime.now().strftime("%Y-%m-%d"),
            "selected_by": None,
            "selected_at": None,
        }
        enrich_with_team(entry, recommender)

        # 추천팀 0건 → TENOPA 사업 영역과 무관한 공고 → 스킵
        if recommender and not entry.get("recommended_teams"):
            skipped_no_team += 1
            continue

        pipeline["active_bids"].append(entry)
        added += 1

    if skipped_no_team:
        print(f"  -> {skipped_no_team}건 제외 (추천팀 없음, 사업영역 무관)")

    pipeline["stats"]["total_scanned"] += len(all_bids)
    pipeline["stats"]["total_recommended"] += added
    pipeline["last_scan"] = datetime.now().isoformat(timespec="seconds")

    # 스코어 내림차순 정렬
    pipeline["active_bids"].sort(key=lambda x: x["score"], reverse=True)
    return added


# ── 과제 선택 ──────────────────────────────────

def select_bid(pipeline: dict, bid_no: str, by: str) -> bool:
    for bid in pipeline["active_bids"]:
        if bid["bid_no"] == bid_no:
            bid["status"] = "selected"
            bid["selected_by"] = by
            bid["selected_at"] = datetime.now().isoformat(timespec="seconds")
            pipeline["stats"]["total_selected"] += 1
            return True
    return False


# ── 출력 ────────────────────────────────────────

def print_active(pipeline: dict, limit: int = 20):
    bids = pipeline["active_bids"]
    if not bids:
        print("  활성 공고가 없습니다.")
        return

    for i, b in enumerate(bids[:limit]):
        status_mark = "★" if b["status"] == "selected" else "●" if b["status"] == "new" else "○"
        d_str = format_d_day(b.get("d_days")) if "d_days" in b else ""
        if not d_str:
            from scripts.bid_scoring import days_until_deadline
            d_days = days_until_deadline(b.get("deadline", ""))
            d_str = format_d_day(d_days)

        print(f"{status_mark} [{b['score']}점] {b['title']}")
        print(f"   발주: {b['client']}  예산: {format_budget(b['budget'])}  마감: {d_str}")
        if b["matched_keywords"]:
            print(f"   키워드: {', '.join(b['matched_keywords'][:5])}")
        # 추천팀 표시
        rec_teams = b.get("recommended_teams", [])
        if rec_teams:
            team_strs = [f"{t['team']}({t['score']}점)" for t in rec_teams[:3]]
            print(f"   → 추천팀: {' | '.join(team_strs)}")
        if b["status"] == "selected":
            print(f"   → 선택: {b['selected_by']} ({b['selected_at']})")
        print()

    if len(bids) > limit:
        print(f"  ... 외 {len(bids) - limit}건")

    stats = pipeline["stats"]
    selected_count = sum(1 for b in bids if b["status"] == "selected")
    print(f"\n총 {len(bids)}건 활성 (선택 {selected_count}건) / "
          f"누적 스캔 {stats['total_scanned']}건, 추천 {stats['total_recommended']}건, "
          f"마감이동 {stats['total_expired']}건")


# ── 메인 ────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="일일 공고 모니터링 + 파이프라인 관리")
    parser.add_argument("--init", action="store_true", help="최초 14일 전수 조회")
    parser.add_argument("--list", action="store_true", help="현재 활성 공고 보기")
    parser.add_argument("--cleanup", action="store_true", help="마감 공고 정리만")
    parser.add_argument("--enrich", action="store_true", help="기존 공고에 팀 추천 추가")
    parser.add_argument("--select", type=str, help="과제 선택 (공고번호)")
    parser.add_argument("--by", type=str, default="", help="선택자 이름")
    args = parser.parse_args()

    from scripts.bid_scoring import PROFILE_PATH
    if not PROFILE_PATH.exists():
        print(f"[ERROR] 역량 프로필 없음: {PROFILE_PATH}")
        print("먼저 import_project_history.py를 실행하세요.")
        sys.exit(1)

    profile = load_profile()
    pipeline = load_pipeline()

    # ── --enrich: 기존 공고에 팀 추천 추가
    if args.enrich:
        recommender = _get_recommender()
        if not recommender:
            print("[ERROR] data/team_structure.json 없음. import_team_structure.py를 먼저 실행하세요.")
            sys.exit(1)
        count = 0
        for bid in pipeline["active_bids"]:
            enrich_with_team(bid, recommender)
            count += 1
        save_pipeline(pipeline)
        print(f"[OK] {count}건 공고에 팀 추천 추가 완료")
        return

    # ── --list: 현재 활성 공고 보기
    if args.list:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        last = pipeline.get("last_scan", "없음")
        print(f"\n━━━ 공고 파이프라인 ({now}) ━━━")
        print(f"마지막 스캔: {last}\n")
        print_active(pipeline)
        return

    # ── --select: 과제 선택
    if args.select:
        if not args.by:
            print("[ERROR] --by 선택자 이름을 지정하세요.")
            sys.exit(1)
        if select_bid(pipeline, args.select, args.by):
            save_pipeline(pipeline)
            print(f"✓ {args.select} 선택 완료 (by {args.by})")
            print("  이 공고를 제안 파이프라인에 등록하시겠습니까?")
            print("  → uv run python scripts/search_matching_bids.py 에서 상세 확인 가능")
        else:
            print(f"[ERROR] 공고번호 {args.select}을(를) 활성 목록에서 찾을 수 없습니다.")
            sys.exit(1)
        return

    # ── --cleanup: 마감 공고 정리만
    if args.cleanup:
        moved = cleanup_expired(pipeline)
        save_pipeline(pipeline)
        print(f"✓ 마감 공고 {moved}건 archived로 이동")
        return

    # ── 기본: 스캔 (init 또는 증분)
    print(f"역량 프로필 로드: {profile['company']['stats']['total_projects']}건 실적, "
          f"{len(profile['search_keywords'])}개 키워드\n")

    recommender = _get_recommender()
    if recommender:
        n_teams = len(recommender.team_data.get("teams", []))
        print(f"팀 추천 활성화: {n_teams}개 팀\n")

    # 마감 공고 정리
    moved = cleanup_expired(pipeline)
    if moved:
        print(f"  마감 공고 {moved}건 정리 완료\n")

    # 스캔
    added = asyncio.run(scan(profile, pipeline, init=args.init, recommender=recommender))

    save_pipeline(pipeline)

    print("\n━━━ 스캔 결과 ━━━")
    print(f"  신규 {added}건 추가 (스코어 {MIN_SCORE}점 이상)")
    print(f"  현재 활성 {len(pipeline['active_bids'])}건\n")

    print_active(pipeline)


if __name__ == "__main__":
    main()
