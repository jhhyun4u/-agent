"""
피드백 데이터 시드 스크립트 (Step 4A Gap 3)

사용: uv run python scripts/seed_feedback_data.py
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from app.config import settings
from app.utils.supabase_client import get_async_client


async def seed_feedback_data():
    """피드백 데이터 샘플 생성"""

    client = await get_async_client()

    # 기존 피드백 데이터 삭제 (선택사항)
    # await client.table("feedback_submissions").delete().neq("id", None).execute()

    # 샘플 제안서 ID 조회
    proposals_resp = await client.table("proposals").select("id").limit(1).execute()
    if not proposals_resp.data:
        print("❌ 제안서가 없습니다. 먼저 제안서를 생성하세요.")
        return

    proposal_id = proposals_resp.data[0]["id"]

    # 샘플 사용자 ID 조회
    users_resp = await client.table("users").select("id").limit(1).execute()
    if not users_resp.data:
        print("❌ 사용자가 없습니다.")
        return

    user_id = users_resp.data[0]["id"]

    # 샘플 피드백 데이터
    feedback_samples = [
        # Executive Summary - 높은 품질
        {
            "proposal_id": proposal_id,
            "section_type": "executive_summary",
            "decision": "APPROVE",
            "ratings": {
                "hallucination": 4.8,
                "persuasiveness": 4.7,
                "completeness": 4.6,
                "clarity": 4.8,
            },
            "comment": "명확하고 설득력 있는 경영진 요약",
            "created_by": user_id,
            "created_at": (datetime.now() - timedelta(days=6)).isoformat(),
        },
        # Technical Approach - 낮은 품질
        {
            "proposal_id": proposal_id,
            "section_type": "technical_approach",
            "decision": "REJECT",
            "ratings": {
                "hallucination": 2.2,
                "persuasiveness": 2.4,
                "completeness": 2.1,
                "clarity": 2.3,
            },
            "comment": "기술적 깊이가 부족함. 더 구체적인 내용 필요",
            "created_by": user_id,
            "created_at": (datetime.now() - timedelta(days=5)).isoformat(),
        },
        # Executive Summary - 재검토 후 승인
        {
            "proposal_id": proposal_id,
            "section_type": "executive_summary",
            "decision": "APPROVE",
            "ratings": {
                "hallucination": 4.5,
                "persuasiveness": 4.6,
                "completeness": 4.4,
                "clarity": 4.7,
            },
            "comment": "수정 후 개선됨",
            "created_by": user_id,
            "created_at": (datetime.now() - timedelta(days=4)).isoformat(),
        },
        # Implementation Plan - 중간 품질
        {
            "proposal_id": proposal_id,
            "section_type": "implementation_plan",
            "decision": "APPROVE",
            "ratings": {
                "hallucination": 3.7,
                "persuasiveness": 3.5,
                "completeness": 3.8,
                "clarity": 3.6,
            },
            "comment": "기본적으로 양호하나 일정 부분 추가 설명 권장",
            "created_by": user_id,
            "created_at": (datetime.now() - timedelta(days=3)).isoformat(),
        },
        # Technical Approach - 재검토 후 거부
        {
            "proposal_id": proposal_id,
            "section_type": "technical_approach",
            "decision": "REJECT",
            "ratings": {
                "hallucination": 2.3,
                "persuasiveness": 2.5,
                "completeness": 2.2,
                "clarity": 2.4,
            },
            "comment": "여전히 기술적 신뢰성이 부족함",
            "created_by": user_id,
            "created_at": (datetime.now() - timedelta(days=2)).isoformat(),
        },
        # Benefits - 높은 품질
        {
            "proposal_id": proposal_id,
            "section_type": "benefits",
            "decision": "APPROVE",
            "ratings": {
                "hallucination": 4.4,
                "persuasiveness": 4.8,
                "completeness": 4.3,
                "clarity": 4.5,
            },
            "comment": "고객 혜택이 명확하게 제시됨",
            "created_by": user_id,
            "created_at": (datetime.now() - timedelta(days=1)).isoformat(),
        },
        # Cost Proposal - 낮은 품질
        {
            "proposal_id": proposal_id,
            "section_type": "cost_proposal",
            "decision": "REJECT",
            "ratings": {
                "hallucination": 2.8,
                "persuasiveness": 2.6,
                "completeness": 2.7,
                "clarity": 2.5,
            },
            "comment": "가격 정당성 설명 부족",
            "created_by": user_id,
            "created_at": datetime.now().isoformat(),
        },
    ]

    # 데이터 삽입
    try:
        response = await client.table("feedback_submissions").insert(
            feedback_samples
        ).execute()

        inserted = len(response.data) if response.data else 0
        print(f"✅ 피드백 데이터 생성 완료: {inserted}개")

        # 분석 결과 출력
        from app.services.domains.proposal.feedback_analyzer import FeedbackAnalyzer

        analyzer = FeedbackAnalyzer()
        analysis = analyzer.analyze_weekly_feedback(response.data)

        print(f"\n📊 분석 결과:")
        print(f"  - 총 피드백: {analysis['total_feedback']}개")
        print(f"  - 전체 승인률: {analysis['summary']['overall_approval_rate']*100:.1f}%")
        print(f"  - 주의 필요 섹션: {', '.join(analysis['summary']['sections_needing_attention']) or '없음'}")
        print(f"  - 우수 섹션: {', '.join(analysis['summary']['sections_performing_well']) or '없음'}")
        print(f"  - 권장사항: {analysis['summary']['next_action']}")

        print(f"\n📋 섹션별 분석:")
        for stat in analysis["section_stats"]:
            print(
                f"  [{stat['section_type']}] "
                f"승인률: {stat['approval_rate']*100:.0f}% "
                f"(승인: {stat['approved']}/{stat['total_feedback']})"
            )

    except Exception as e:
        print(f"❌ 데이터 생성 실패: {e}")
        raise


async def verify_migration():
    """마이그레이션 확인"""
    try:
        client = await get_async_client()

        # 테이블 존재 확인
        result = await client.table("feedback_submissions").select(
            "id"
        ).limit(1).execute()

        print("✅ 피드백 테이블 확인 완료")
        return True

    except Exception as e:
        print(f"❌ 마이그레이션 필요: {e}")
        print("\n다음 명령을 Supabase SQL 에디터에서 실행하세요:")
        print("  cat database/migrations/005_feedback_submissions.sql")
        return False


async def main():
    """메인 실행"""
    print("🔄 피드백 데이터 시드 스크립트\n")

    # 마이그레이션 확인
    if not await verify_migration():
        return

    # 데이터 생성
    await seed_feedback_data()

    print("\n✅ 완료!")


if __name__ == "__main__":
    asyncio.run(main())
