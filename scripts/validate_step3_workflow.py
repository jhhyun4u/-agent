#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
STEP 3 (팀/담당/일정/스토리) 검증 스크립트

목표:
- STEP 2 전략 출력을 시뮬레이션한 입력 데이터 준비
- STEP 3 5개 병렬 노드 호출 (plan_team, plan_assign, plan_schedule, plan_story, proposal_customer_analysis)
- 출력 검증
- 결과 리포트 생성
"""

import asyncio
import io
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any
from uuid import uuid4

# UTF-8 출력 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.graph.state import (
    ProposalState,
    RFPAnalysis,
    GoNoGoResult,
    Strategy,
    StrategyAlternative,
)


# ─────────────────────────────────────────────
# STEP 2 출력 시뮬레이션 (STEP 3 입력용)
# ─────────────────────────────────────────────

def create_test_strategy() -> Strategy:
    """STEP 2 출력 시뮬레이션: 생성된 전략"""
    alt1 = StrategyAlternative(
        alt_id="alt_001",
        ghost_theme="경쟁사: 기존 온프레미스 기반, 운영 경험 부족",
        win_theme=(
            "우리: 클라우드-네이티브 아키텍처, "
            "마이크로서비스 기반으로 유연성·확장성 우수. "
            "Kubernetes 운영 경험 5년, SRE 팀 10명 보유."
        ),
        action_forcing_event=(
            "정부 클라우드 마이그레이션 정책(2026) + "
            "레거시 시스템 EOL(2027) → "
            "2026년 내 의사결정 필수"
        ),
        key_messages=[
            "클라우드 네이티브로 즉시 50% 성능 향상",
            "자동 스케일링으로 연간 ₩200M 비용 절감",
            "DevOps 통합으로 운영 인력 30% 절감",
            "24/7 SLA 99.95% 보장",
        ],
        price_strategy={
            "approach": "innovation_premium",
            "ratio": 88,  # 낙찰률 88%
            "reasoning": "기술 혁신가치로 프리미엄 정당화",
        },
        risk_assessment={
            "risks": [
                "마이그레이션 복잡도 (400+ 애플리케이션)",
                "레거시 통합 이슈 (20% 호환성 위험)",
                "운영팀 학습곡선 (3개월)",
            ],
            "mitigation": [
                "단계적 마이그레이션 (3단계)",
                "호환성 계층 구축",
                "교육 프로그램 6주 (50명)",
            ],
        },
    )

    alt2 = StrategyAlternative(
        alt_id="alt_002",
        ghost_theme="우리: 초기 투자비용 높음 (초기구축 ₩150M)",
        win_theme=(
            "안정성+신뢰: 정부기관 40건 수행실적. "
            "국내 최초 클라우드 도입기관 3곳(2019). "
            "SLA 달성률 99.98% (5년 누적)."
        ),
        action_forcing_event=(
            "ISMS 인증 의무화(2026.07) → "
            "지금부터 운영 체계 수립 필수"
        ),
        key_messages=[
            "정부 기관 신뢰도 #1: 40건 수행실적",
            "안정적 운영: 5년 99.98% SLA 달성",
            "검증된 아키텍처: 초기 위험 최소화",
            "교육·지원 풀 투입: 안정적 전환",
        ],
        price_strategy={
            "approach": "stability_premium",
            "ratio": 92,  # 낙찰률 92%
            "reasoning": "신뢰·안정성으로 높은 낙찰률 기대",
        },
        risk_assessment={
            "risks": [
                "높은 초기 구축비용 (ROI 3년)",
                "기술 최신성 부족 (관리형 서비스)",
                "향후 확장성 제약",
            ],
            "mitigation": [
                "분할 납부 조건 협상",
                "업그레이드 계약 포함",
                "확장 옵션 사전 설계",
            ],
        },
    )

    return Strategy(
        positioning="offensive",
        positioning_rationale=(
            "경쟁사 대비 우수한 클라우드 아키텍처 경험과 "
            "정부기관 신뢰 기반으로 혁신성과 안정성 모두 겸비."
        ),
        alternatives=[alt1, alt2],
        focus_areas=[
            {"area": "기술 혁신", "focus": "클라우드 네이티브 아키텍처"},
            {"area": "안정성", "focus": "99.95% SLA 보증"},
            {"area": "비용 효율", "focus": "연간 ₩200M 절감"},
        ],
    )


def create_test_rfp_analysis() -> RFPAnalysis:
    """RFP 분석 결과 (STEP 3 입력)"""
    return RFPAnalysis(
        project_name="정부 클라우드 플랫폼 마이그레이션 및 운영 구축",
        client="과학기술정보통신부",
        case_type="A",
        deadline=(datetime.now() + timedelta(days=45)).isoformat(),
        eval_method="종합심사",
        eval_items=[
            {"name": "기술점", "weight": 40, "max_score": 100},
            {"name": "가격점", "weight": 30, "max_score": 100},
            {"name": "실적점", "weight": 20, "max_score": 100},
            {"name": "가산점", "weight": 10, "max_score": 20},
        ],
        tech_price_ratio={"tech_weight": 40, "price_weight": 30},
        hot_buttons=[
            "기술 혁신 및 차별화",
            "대규모 프로젝트 경험",
            "24/7 운영 역량",
            "보안 및 규정 준수",
        ],
        mandatory_reqs=[
            "정보보호관리체계(ISMS) 인증",
            "클라우드 보안 기준 준수",
        ],
        format_template={
            "section1": "기술 제안",
            "section2": "운영 계획",
            "section3": "가격 제안",
        },
        volume_spec={
            "max_pages": 150,
            "format": "HWP",
        },
        special_conditions=[
            "발표: 2시간 (기술+가격)",
            "보증금: 추정가격의 5%",
        ],
        domain="클라우드/마이그레이션",
        budget="800,000,000",
        duration="12개월",
        contract_type="정액",
    )


def create_test_proposal_state() -> ProposalState:
    """STEP 3 입력 데이터 준비"""
    state = ProposalState(
        project_id=str(uuid4()),
        org_id="test-org-001",
        rfp_analysis=create_test_rfp_analysis(),
        go_no_go=GoNoGoResult(
            positioning="offensive",
            positioning_rationale="기술 혁신 + 안정적 운영",
            feasibility_score=85,
            score_breakdown={
                "qualification": 90,
                "performance": 85,
                "competition": 75,
                "risk": 80,
            },
            pros=[
                "마이크로서비스 아키텍처 5건 이상",
                "대규모 Kubernetes 운영 경험",
            ],
            risks=[
                "실적점 경쟁 심화",
                "가격 경쟁 심화",
            ],
            recommendation="go",
        ),
        strategy=create_test_strategy(),
        current_step="plan_team",
    )
    return state


# ─────────────────────────────────────────────
# STEP 3 검증
# ─────────────────────────────────────────────

async def main():
    print("=" * 100)
    print("STEP 3 (팀/담당/일정/스토리) 워크플로우 검증")
    print("=" * 100)
    print()

    # 테스트 데이터 생성
    print("[1] 테스트 데이터 생성...")
    state = create_test_proposal_state()
    print(f"    - Project ID: {state.get('project_id')}")
    print(f"    - RFP: {state.get('rfp_analysis').project_name if state.get('rfp_analysis') else '(없음)'}")
    print(f"    - Strategy: {state.get('strategy').positioning if state.get('strategy') else '(없음)'}")
    print()

    # STEP 3 노드 구조 분석
    print("[2] STEP 3 노드 구조 분석...")
    print("    STEP 3 구성: 5개 병렬 노드")
    print("    1. plan_team — 팀 구성")
    print("    2. plan_assign — 담당 배정")
    print("    3. plan_schedule — 일정 계획")
    print("    4. plan_story — 스토리라인")
    print("    5. proposal_customer_analysis — 고객 분석")
    print()

    # 각 노드 상세 설명
    print("[3] 각 노드의 역할과 출력")
    print()

    nodes_info = {
        "plan_team": {
            "입력": ["strategy", "rfp_analysis"],
            "출력": ["team_structure", "roles", "responsibilities"],
            "예시": "팀장(1), 기술담당(2), 운영담당(1), QA(1) = 5명",
        },
        "plan_assign": {
            "입력": ["team_structure", "strategy"],
            "출력": ["assignments", "person_roles"],
            "예시": "각 팀원의 담당 영역 상세 배정",
        },
        "plan_schedule": {
            "입력": ["team_structure", "rfp_analysis"],
            "출력": ["schedule", "milestones", "deliverables"],
            "예시": "Phase 1(2개월): 설계 | Phase 2(6개월): 구축 | Phase 3(4개월): 운영",
        },
        "plan_story": {
            "입력": ["strategy", "team_structure"],
            "출력": ["story_structure", "narrative", "key_chapters"],
            "예시": "[Ch1]고객 현황 분석 → [Ch2]우리의 차별 포인트 → [Ch3]구축 계획 → [Ch4]위험 관리",
        },
        "proposal_customer_analysis": {
            "입력": ["rfp_analysis"],
            "출력": ["customer_profile", "pain_points", "success_factors"],
            "예시": "의사결정자(CIO), 실무담당자(PM), 기술담당자(아키텍트)",
        },
    }

    for node_name, info in nodes_info.items():
        print(f"▪ {node_name}")
        print(f"  입력: {', '.join(info['입력'])}")
        print(f"  출력: {', '.join(info['출력'])}")
        print(f"  예시: {info['예시']}")
        print()

    # 검증 기준
    print("=" * 100)
    print("STEP 3 검증 기준")
    print("=" * 100)
    print()

    criteria = {
        "plan_team": [
            "팀 규모 적절성 (예산 기반: ₩800M = 약 5~8명)",
            "역할 정의 명확성",
            "경험 요구사항 명시",
            "총 인력 투입량 타당성",
        ],
        "plan_assign": [
            "각 팀원의 역할 명확성",
            "책임 영역의 중복 없음",
            "선형 종속성 회피",
        ],
        "plan_schedule": [
            "Phase 분할의 논리성",
            "마일스톤 명확성",
            "납기 타당성",
            "위험 완화 계획 포함",
        ],
        "plan_story": [
            "스토리 구조의 설득력",
            "Key Chapter 5~7개",
            "고객 문제→우리 솔루션의 논리 흐름",
            "기술+경영진 모두 납득 가능",
        ],
        "proposal_customer_analysis": [
            "의사결정자 분석",
            "Pain Point 3~5개",
            "Success Factors 명확",
        ],
    }

    for node, checks in criteria.items():
        print(f"[{node}]")
        for check in checks:
            print(f"  - {check}")
        print()

    print("=" * 100)
    print("현재까지 확인된 내용")
    print("=" * 100)
    print()
    print("✓ STEP 2 출력 데이터 준비 완료 (전략 포함)")
    print("✓ STEP 3 입력 데이터 준비 완료")
    print("✓ STEP 3 노드 구조 분석 완료")
    print()
    print("다음 단계:")
    print("1. 실제 STEP 3 노드 호출 및 실행")
    print("2. 각 노드 출력 검증")
    print("3. 통합 검증 리포트 생성")
    print()


if __name__ == "__main__":
    asyncio.run(main())
