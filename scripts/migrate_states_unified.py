"""
통합 상태 시스템 데이터 마이그레이션 스크립트
Migration 019: 기존 16개 분산 상태값 → 10개 통합 비즈니스 상태

실행 방법:
    uv run python scripts/migrate_states_unified.py [--dry-run] [--verbose]

옵션:
    --dry-run   실제 변경 없이 마이그레이션 대상 분석만 수행
    --verbose   각 proposal의 변환 내역 출력

요구 사항:
    - Migration 019_unified_state_system.sql 실행 완료 후 수행
    - SUPABASE_URL, SUPABASE_SERVICE_KEY 환경변수 설정 필요

마이그레이션 매핑 테이블 (기존 → 신규):
    initialized  → waiting
    processing   → in_progress
    searching    → in_progress
    analyzing    → in_progress
    strategizing → in_progress
    completed    → completed
    submitted    → submitted
    presented    → presentation
    won          → closed  (win_result=won)
    lost         → closed  (win_result=lost)
    no_go        → closed  (win_result=no_go)
    abandoned    → closed  (win_result=abandoned)
    retrospect   → closed  (win_result=lost, 교훈 기록 단계 → 종료 처리)
    on_hold      → on_hold
    expired      → expired
    running      → in_progress  (AI 상태 → ai_task_status로 이관)
    failed       → in_progress  (재시도 가능 상태로 복원)
    cancelled    → closed  (win_result=cancelled)
    paused       → on_hold
"""

import asyncio
import argparse
import os
import sys
from datetime import datetime, timezone
from typing import Optional

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# 기존 상태 → (신규 status, win_result) 매핑
STATE_MAPPING: dict[str, tuple[str, Optional[str]]] = {
    # 진행 전 상태
    "initialized":  ("waiting",       None),
    "waiting":      ("waiting",       None),      # 이미 새 값인 경우

    # 진행 중 상태
    "processing":   ("in_progress",   None),
    "searching":    ("in_progress",   None),
    "analyzing":    ("in_progress",   None),
    "strategizing": ("in_progress",   None),
    "running":      ("in_progress",   None),      # AI 임시 상태 → 진행중으로 복원
    "failed":       ("in_progress",   None),      # 실패 → 재시도 가능 상태
    "paused":       ("on_hold",       None),      # 일시중지 → 보류
    "in_progress":  ("in_progress",   None),      # 이미 새 값인 경우

    # 완성 상태
    "completed":    ("completed",     None),      # 이미 새 값인 경우

    # 제출 상태
    "submitted":    ("submitted",     None),      # 이미 새 값인 경우

    # 발표/입찰 상태
    "presented":    ("presentation",  None),
    "presentation": ("presentation",  None),      # 이미 새 값인 경우

    # 종료 상태 (win_result 포함)
    "won":          ("closed",        "won"),
    "lost":         ("closed",        "lost"),
    "no_go":        ("closed",        "no_go"),
    "abandoned":    ("closed",        "abandoned"),
    "retrospect":   ("closed",        "lost"),    # 교훈 기록 단계 → 종료(패찰) 처리
    "cancelled":    ("closed",        "cancelled"),

    # 특수 상태
    "on_hold":      ("on_hold",       None),      # 이미 새 값인 경우
    "expired":      ("expired",       None),      # 이미 새 값인 경우
    "archived":     ("archived",      None),      # 이미 새 값인 경우
    "closed":       ("closed",        None),      # 이미 새 값인 경우 (win_result는 기존 값 유지)
}

# 신규 상태값 (마이그레이션 불필요)
NEW_STATUS_VALUES = {
    "waiting", "in_progress", "completed", "submitted",
    "presentation", "closed", "archived", "on_hold", "expired"
}


async def run_migration(dry_run: bool = False, verbose: bool = False) -> None:
    """마이그레이션 실행

    Args:
        dry_run: True이면 실제 변경 없이 분석만 수행
        verbose: True이면 각 proposal 변환 내역 출력
    """
    from app.utils.supabase_client import get_async_client

    client = await get_async_client()
    now = datetime.now(timezone.utc).isoformat()

    print(f"{'[DRY-RUN] ' if dry_run else ''}통합 상태 시스템 마이그레이션 시작")
    print(f"실행 시각: {now}")
    print("-" * 60)

    # 전체 proposal 조회
    try:
        result = await client.table("proposals").select(
            "id, status, win_result, current_phase, created_at, updated_at"
        ).execute()
    except Exception as e:
        print(f"[ERROR] proposals 테이블 조회 실패: {e}")
        sys.exit(1)

    proposals = result.data or []
    print(f"총 {len(proposals)}건 proposal 조회 완료\n")

    # 통계 카운터
    stats = {
        "skipped":   0,   # 이미 새 상태값
        "migrated":  0,   # 마이그레이션 성공
        "unknown":   0,   # 알 수 없는 상태 (매핑 없음)
        "errors":    0,   # DB 업데이트 오류
    }

    # 상태별 분포 집계
    status_distribution: dict[str, int] = {}
    for p in proposals:
        s = p.get("status", "unknown")
        status_distribution[s] = status_distribution.get(s, 0) + 1

    print("현재 상태 분포:")
    for status, count in sorted(status_distribution.items()):
        indicator = " (신규값)" if status in NEW_STATUS_VALUES else " (구버전)"
        print(f"  {status:<20} {count:>5}건{indicator}")
    print()

    # 각 proposal 마이그레이션
    for proposal in proposals:
        proposal_id = proposal["id"]
        old_status = proposal.get("status", "")
        old_win_result = proposal.get("win_result")

        # 이미 새 상태값이고 win_result 처리가 불필요한 경우 스킵
        if old_status in NEW_STATUS_VALUES and old_status != "closed":
            stats["skipped"] += 1
            if verbose:
                print(f"  SKIP  {proposal_id}: {old_status} (이미 새 값)")
            continue

        # closed 상태는 win_result가 이미 있으면 스킵
        if old_status == "closed" and old_win_result is not None:
            stats["skipped"] += 1
            if verbose:
                print(f"  SKIP  {proposal_id}: closed (win_result={old_win_result})")
            continue

        # 매핑 조회
        if old_status not in STATE_MAPPING:
            print(f"  [WARN] {proposal_id}: 알 수 없는 상태 '{old_status}' — 스킵")
            stats["unknown"] += 1
            continue

        new_status, new_win_result = STATE_MAPPING[old_status]

        # closed 상태인데 win_result 매핑이 없으면 기존 값 유지
        if new_status == "closed" and new_win_result is None and old_win_result:
            new_win_result = old_win_result

        if verbose:
            wr_info = f" → win_result={new_win_result}" if new_win_result else ""
            print(f"  MIGRATE {proposal_id}: {old_status} → {new_status}{wr_info}")

        if dry_run:
            stats["migrated"] += 1
            continue

        # DB 업데이트
        try:
            update_data: dict = {
                "status": new_status,
                "last_activity_at": now,
            }

            if new_win_result:
                update_data["win_result"] = new_win_result

            # 타임스탬프 보정: closed/archived/expired 상태에 대해 종료 시간 설정
            if new_status == "closed" and not proposal.get("closed_at"):
                update_data["closed_at"] = proposal.get("updated_at") or now
            if new_status == "archived" and not proposal.get("archived_at"):
                update_data["archived_at"] = proposal.get("updated_at") or now
            if new_status == "expired" and not proposal.get("expired_at"):
                update_data["expired_at"] = proposal.get("updated_at") or now
            if new_status == "in_progress" and not proposal.get("started_at"):
                update_data["started_at"] = proposal.get("updated_at") or now

            await client.table("proposals").update(update_data).eq("id", proposal_id).execute()

            # proposal_timelines에 마이그레이션 이벤트 기록
            timeline_entry = {
                "proposal_id": proposal_id,
                "event_type": "status_change",
                "from_status": old_status,
                "to_status": new_status,
                "actor_type": "system",
                "trigger_reason": f"통합 상태 시스템 마이그레이션 (019): {old_status} → {new_status}",
                "metadata": {
                    "migration_script": "migrate_states_unified.py",
                    "migration_date": now,
                    **({"win_result": new_win_result} if new_win_result else {}),
                },
                "created_at": now,
            }
            await client.table("proposal_timelines").insert(timeline_entry).execute()

            # running 상태 proposal은 ai_task_status에도 기록
            if old_status == "running":
                ai_entry = {
                    "proposal_id": proposal_id,
                    "status": "error",   # 재시작 필요 상태로 표시
                    "error_message": "서버 재시작/마이그레이션으로 인한 AI 작업 중단",
                    "started_at": proposal.get("updated_at") or now,
                    "ended_at": now,
                }
                await client.table("ai_task_status").insert(ai_entry).execute()

            stats["migrated"] += 1

        except Exception as e:
            print(f"  [ERROR] {proposal_id}: 업데이트 실패 — {e}")
            stats["errors"] += 1

    # 결과 요약
    print("\n" + "=" * 60)
    print(f"{'[DRY-RUN] ' if dry_run else ''}마이그레이션 완료")
    print(f"  스킵 (이미 새 값): {stats['skipped']:>5}건")
    print(f"  마이그레이션 성공: {stats['migrated']:>5}건")
    print(f"  알 수 없는 상태:   {stats['unknown']:>5}건")
    print(f"  오류:              {stats['errors']:>5}건")
    print("=" * 60)

    if stats["errors"] > 0:
        print(f"\n[WARNING] {stats['errors']}건 오류 발생. 로그를 확인하세요.")
        sys.exit(1)

    if not dry_run and stats["migrated"] > 0:
        print("\n다음 단계:")
        print("  1. 데이터 무결성 확인:")
        print("     SELECT COUNT(*) FROM proposals WHERE status NOT IN")
        print("       ('waiting','in_progress','completed','submitted',")
        print("        'presentation','closed','archived','on_hold','expired');")
        print("     -- 예상: 0")
        print("  2. routes_workflow.py 에서 status='running'/'cancelled' 코드 제거")
        print("  3. ruff check app/ && mypy app/ 실행")


def main() -> None:
    """CLI 진입점"""
    parser = argparse.ArgumentParser(
        description="통합 상태 시스템 데이터 마이그레이션 (019)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="실제 변경 없이 마이그레이션 대상 분석만 수행",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="각 proposal의 변환 내역 출력",
    )
    args = parser.parse_args()

    asyncio.run(run_migration(dry_run=args.dry_run, verbose=args.verbose))


if __name__ == "__main__":
    main()
