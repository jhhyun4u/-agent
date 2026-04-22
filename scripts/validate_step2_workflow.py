#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
STEP 2 (포지셔닝/전략) 검증 스크립트

목표:
- STEP 0/1 출력을 시뮬레이션한 입력 데이터 준비
- STEP 2 strategy_generate 함수 호출
- 출력 검증 (10-point checklist)
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
from app.graph.nodes.strategy_generate import strategy_generate


# ─────────────────────────────────────────────
# 테스트 케이스: 정부 클라우드 통합 프로젝트
# ─────────────────────────────────────────────

def create_test_rfp_analysis() -> RFPAnalysis:
    """STEP 1 출력 시뮬레이션: RFP 분석"""
    return RFPAnalysis(
        project_name="정부 클라우드 플랫폼 마이그레이션 및 운영 구축",
        client="과학기술정보통신부",
        case_type="A",  # A or B case
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
            "개인정보 암호화 필수",
            "감시 로깅 및 감사 추적",
        ],
        format_template={
            "section1": "기술 제안",
            "section2": "운영 계획",
            "section3": "가격 제안",
        },
        volume_spec={
            "max_pages": 150,
            "format": "HWP",
            "font": "신명조",
            "font_size": 11,
        },
        special_conditions=[
            "제출물: 서면 150매 + 전자파일 PDF",
            "발표: 2시간 (기술+가격)",
            "보증금: 추정가격의 5%",
        ],
        # 확장 필드
        domain="클라우드/마이그레이션",
        project_scope="기존 정부 정보시스템을 클라우드로 마이그레이션하고 12개월 운영 관리",
        budget="800,000,000",
        duration="12개월 (2026.07~2027.06)",
        contract_type="정액",
        delivery_phases=[
            {"phase": "1", "name": "설계", "months": 2, "deliverables": ["아키텍처 설계서", "인프라 구성도"]},
            {"phase": "2", "name": "구축", "months": 6, "deliverables": ["클라우드 환경", "통합 테스트"]},
            {"phase": "3", "name": "운영", "months": 4, "deliverables": ["운영 보고서", "최종 인수증"]},
        ],
    )


def create_test_go_no_go() -> GoNoGoResult:
    """STEP 1 출력 시뮬레이션: Go/No-Go 판정"""
    return GoNoGoResult(
        positioning="offensive",  # 혁신·차별화 포지셔닝 선택
        positioning_rationale=(
            "경쟁사 대비 우수한 클라우드 아키텍처 경험 보유. "
            "마이크로서비스 및 컨테이너 기술에서 차별화 가능. "
            "초저지연 네트워크 설계 기술로 경쟁 우위 확보 가능."
        ),
        feasibility_score=85,  # 4축 합산 (0~100)
        score_breakdown={
            "qualification": 90,  # 자격 적격성
            "performance": 85,    # 유사실적
            "competition": 75,    # 경쟁 강도
            "risk": 80,          # 위험도
        },
        pros=[
            "마이크로서비스 아키텍처 설계 경험 5건 이상",
            "대규모 Kubernetes 클러스터 운영 경험",
            "AWS/Azure 복수 클라우드 통합 경험",
            "정보보호관리 경험 (ISMS 인증 5개 건)",
            "정부 프로젝트 납기율 98% 이상",
        ],
        risks=[
            "평가자 점수에서 실적점 경쟁 심화 우려",
            "낙찰률 예상 85~92% 범위 (가격 경쟁 심화)",
            "운영 인력 투입 규모 (월 200인시 예상)",
            "클라우드 운영 SLA 이행 위험 (24/7 체제 필요)",
        ],
        recommendation="go",
        strategic_focus="기술혁신 + 안정적 운영",
        score_tag="standard",
    )


def create_test_research_brief() -> Dict[str, Any]:
    """STEP 1 출력 시뮬레이션: 리서치 브리프"""
    return {
        "market_research": [
            {
                "source": "451 Research",
                "title": "Enterprise Cloud Adoption Index 2026",
                "key_insight": "정부 클라우드 마이그레이션 시장 연평균 15% 성장",
                "relevance": "high",
                "evidence": 85,
            },
            {
                "source": "Gartner",
                "title": "Magic Quadrant for Cloud Infrastructure and Platforms",
                "key_insight": "AWS 시장 점유율 32%, Azure 23%, GCP 11% (2026년 기준)",
                "relevance": "high",
                "evidence": 90,
            },
            {
                "source": "IDC",
                "title": "한국 정부 기관 IT 현대화 투자 방향",
                "key_insight": "정부 기관 75%가 클라우드 마이그레이션 3년 내 추진",
                "relevance": "high",
                "evidence": 88,
            },
        ],
        "client_research": [
            {
                "source": "정부혁신전략회의 2025",
                "title": "Digital Government 전략",
                "key_insight": "K-클라우드 확대, 공동활용 인프라 구축",
                "relevance": "high",
                "evidence": 92,
            },
        ],
        "competitor_research": [
            {
                "source": "낙찰가 정보 (2024-2025)",
                "title": "유사 클라우드 구축 사업 낙찰 분석",
                "key_insight": "SK C&C: 4건, 낙찰율 89% 평균. LG CNS: 3건, 89.5% 평균",
                "relevance": "high",
                "evidence": 88,
            },
        ],
    }


def create_test_proposal_state() -> ProposalState:
    """전체 ProposalState 생성 (STEP 2 입력)"""
    state = ProposalState(
        project_id=str(uuid4()),
        org_id="test-org-001",
        rfp_analysis=create_test_rfp_analysis(),
        go_no_go=create_test_go_no_go(),
        positioning="offensive",
        research_brief=create_test_research_brief(),
        current_step="strategy_generate",
    )
    return state


# ─────────────────────────────────────────────
# 10-Point Validation Checklist
# ─────────────────────────────────────────────

def validate_strategy_output(strategy: Strategy) -> Dict[str, Any]:
    """STEP 2 출력 검증"""

    issues = []
    findings = {
        "json_format_valid": False,
        "win_theme_quality": "",
        "ghost_theme_present": False,
        "afe_uniqueness": "",
        "key_messages_clarity": "",
        "price_strategy_valid": False,
        "competitor_analysis_depth": 0,
        "research_framework_present": False,
        "alternatives_differentiated": False,
        "performance_metrics": {
            "alternative_count": 0,
            "avg_win_theme_length": 0,
            "avg_key_messages_per_alt": 0,
        },
    }

    try:
        # 1. JSON 포맷 검증
        assert isinstance(strategy, Strategy), "Strategy 타입 오류"
        assert strategy.positioning is not None, "positioning 필드 누락"

        # alternatives가 None일 수도 있으므로 처리
        alts = strategy.alternatives or []
        assert isinstance(alts, list), "alternatives 타입 오류"

        if len(alts) >= 2:
            findings["json_format_valid"] = True
        else:
            issues.append(f"대안 {len(alts)}개만 제시 (2개 이상 필요)")

        # 2. Win Theme 품질
        for alt in alts:
            if alt and alt.win_theme:
                wt_len = len(alt.win_theme)
                if wt_len > 200:
                    findings["win_theme_quality"] = "good"
                elif wt_len > 80:
                    findings["win_theme_quality"] = "acceptable"
                else:
                    issues.append(f"Win Theme 너무 짧음 ({wt_len}자)")

        # 3. Ghost Theme 검증
        for alt in alts:
            if alt and alt.ghost_theme and len(alt.ghost_theme) > 50:
                findings["ghost_theme_present"] = True
                break

        # 4. Action Forcing Event (AFE) 검증
        afe_count = sum(1 for alt in alts if alt and alt.action_forcing_event)
        alt_len = len([a for a in alts if a])
        if alt_len > 0:
            if afe_count == alt_len:
                findings["afe_uniqueness"] = "good"
            elif afe_count > 0:
                findings["afe_uniqueness"] = "partial"
                issues.append(f"AFE {afe_count}/{alt_len}개만 정의됨")
            else:
                issues.append("AFE가 정의되지 않음")

        # 5. Key Messages 검증
        msg_count = sum(len(alt.key_messages or []) for alt in alts if alt)
        if msg_count >= 6:
            findings["key_messages_clarity"] = "good"
        elif msg_count >= 3:
            findings["key_messages_clarity"] = "acceptable"
        else:
            issues.append(f"Key Messages 부족 ({msg_count}개)")

        # 6. Price Strategy 검증
        price_strategies = [alt.price_strategy for alt in alts if alt and alt.price_strategy]
        if alt_len > 0 and len(price_strategies) == alt_len:
            findings["price_strategy_valid"] = True
        elif alt_len > 0:
            issues.append(f"Price Strategy {len(price_strategies)}/{alt_len}개만 정의")

        # 7. Competitor Analysis 깊이
        comp_depth = 0
        if strategy.competitor_analysis:
            comp_text = str(strategy.competitor_analysis)
            if "SWOT" in comp_text:
                comp_depth += 2
            if "차별화" in comp_text or "differentiation" in comp_text:
                comp_depth += 2
            if "전략" in comp_text or "strategy" in comp_text:
                comp_depth += 1
        findings["competitor_analysis_depth"] = comp_depth

        # 8. Research Framework 검증
        if strategy.research_framework and len(str(strategy.research_framework)) > 100:
            findings["research_framework_present"] = True
        else:
            issues.append("Research Framework 미흡")

        # 9. 대안 차별화
        valid_alts = [a for a in alts if a]
        if len(valid_alts) >= 2:
            alt1_tone = str(valid_alts[0].positioning_tone or "").lower()
            alt2_tone = str(valid_alts[1].positioning_tone or "").lower()
            if alt1_tone != alt2_tone and alt1_tone and alt2_tone:
                findings["alternatives_differentiated"] = True
            else:
                issues.append("대안 간 차별화 미흡")

        # 10. 성능 지표
        alt_count = len(valid_alts)
        findings["performance_metrics"] = {
            "alternative_count": alt_count,
            "avg_win_theme_length": sum(
                len(alt.win_theme or "") for alt in valid_alts
            ) // alt_count if alt_count > 0 else 0,
            "avg_key_messages_per_alt": msg_count / alt_count if alt_count > 0 else 0,
        }

    except AssertionError as e:
        issues.append(str(e))
    except Exception as e:
        issues.append(f"검증 오류: {e}")

    findings["issues"] = issues
    findings["validation_score"] = sum([
        findings["json_format_valid"],
        bool(findings["win_theme_quality"]),
        findings["ghost_theme_present"],
        bool(findings["afe_uniqueness"]),
        bool(findings["key_messages_clarity"]),
        findings["price_strategy_valid"],
        findings["research_framework_present"],
        findings["alternatives_differentiated"],
    ]) / 8 * 100

    return findings


# ─────────────────────────────────────────────
# 메인 실행
# ─────────────────────────────────────────────

async def main():
    print("=" * 100)
    print("STEP 2 (포지셔닝/전략) 워크플로우 검증")
    print("=" * 100)
    print()

    # 테스트 데이터 생성
    print("[1] 테스트 데이터 생성...")
    state = create_test_proposal_state()
    rfp = state.get('rfp_analysis')
    print(f"    - Project ID: {state.get('project_id')}")
    print(f"    - RFP: {rfp.project_name if rfp else '(없음)'}")
    print(f"    - Positioning: {state.get('positioning')}")
    print()

    # STEP 2 실행
    print("[2] STEP 2 strategy_generate 실행 중...")
    try:
        result = await strategy_generate(state)

        # DEBUG: 원본 결과 출력
        import json as _json
        print(f"\n[DEBUG] Claude 응답 구조:")
        print(f"  - 최상위 키: {list(result.keys())[:5]}")
        if "strategy" in result:
            strat = result["strategy"]
            print(f"  - strategy 타입: {type(strat).__name__}")
            if hasattr(strat, "alternatives"):
                alts = strat.alternatives or []
                print(f"  - strategy.alternatives 개수: {len(alts)}")
                if alts:
                    for i, alt in enumerate(alts, 1):
                        print(f"    [대안 {i}]")
                        print(f"      - alt_id: {alt.alt_id if hasattr(alt, 'alt_id') else '(없음)'}")
                        win_theme = alt.win_theme if hasattr(alt, 'win_theme') else ""
                        print(f"      - win_theme 길이: {len(win_theme)} 자")
                        if win_theme:
                            print(f"      - win_theme 미리보기: {win_theme[:100]}...")
                        key_msgs = alt.key_messages if hasattr(alt, 'key_messages') else []
                        print(f"      - key_messages: {len(key_msgs) if key_msgs else 0}개")
        print()

        strategy = result.get("strategy")

        if not strategy:
            print("    [FAIL] strategy 생성 실패")
            return

        print(f"    [OK] Strategy 생성 완료")
        print()

        # 검증
        print("[3] 10-Point 검증 체크리스트 실행...")
        findings = validate_strategy_output(strategy)

        print()
        print("=" * 100)
        print("검증 결과")
        print("=" * 100)
        print()

        # 체크리스트 출력
        checklist = [
            ("[OK]" if findings["json_format_valid"] else "[FAIL]", "JSON 포맷 유효성"),
            ("[OK]" if findings["win_theme_quality"] else "[FAIL]", f"Win Theme 품질 ({findings['win_theme_quality']})"),
            ("[OK]" if findings["ghost_theme_present"] else "[FAIL]", "Ghost Theme 현재"),
            ("[OK]" if findings["afe_uniqueness"] else "[FAIL]", f"AFE 정의 ({findings['afe_uniqueness']})"),
            ("[OK]" if findings["key_messages_clarity"] else "[FAIL]", f"Key Messages ({findings['key_messages_clarity']})"),
            ("[OK]" if findings["price_strategy_valid"] else "[FAIL]", "Price Strategy 유효"),
            ("[PARTIAL]" if findings["competitor_analysis_depth"] > 0 else "[FAIL]", f"Competitor Analysis (깊이={findings['competitor_analysis_depth']})"),
            ("[OK]" if findings["research_framework_present"] else "[FAIL]", "Research Framework"),
            ("[OK]" if findings["alternatives_differentiated"] else "[FAIL]", "대안 차별화"),
            ("[OK]", f"성능 지표 기록 (대안={findings['performance_metrics']['alternative_count']}개)"),
        ]

        for symbol, desc in checklist:
            print(f"{symbol} {desc}")

        print()
        print(f"검증 점수: {findings['validation_score']:.1f}/100")
        print()

        # 이슈 리포트
        if findings["issues"]:
            print("발견된 이슈:")
            for i, issue in enumerate(findings["issues"], 1):
                print(f"  {i}. {issue}")
            print()

        # Strategy 상세 출력
        print("=" * 100)
        print("생성된 Strategy 상세")
        print("=" * 100)
        print()
        print(f"Positioning: {strategy.positioning if strategy else '(없음)'}")
        if strategy and strategy.positioning_rationale:
            print(f"포지셔닝 근거: {strategy.positioning_rationale[:200]}...")
        print()

        alts = strategy.alternatives or []
        for i, alt in enumerate(alts, 1):
            if not alt:
                continue
            print(f"[대안 {i}]")
            print(f"  - ID: {alt.alt_id if alt.alt_id else '(없음)'}")
            print(f"  - Positioning: {alt.positioning_tone if hasattr(alt, 'positioning_tone') else '(없음)'}")
            if alt.win_theme:
                print(f"  - Win Theme: {alt.win_theme[:150]}...")
            if alt.ghost_theme:
                print(f"  - Ghost Theme: {alt.ghost_theme[:100]}...")
            if alt.action_forcing_event:
                print(f"  - AFE: {alt.action_forcing_event[:100]}...")
            print(f"  - Key Messages: {len(alt.key_messages or [])}개")
            if alt.price_strategy:
                print(f"  - Price Strategy: {str(alt.price_strategy)[:100]}...")
            print()

        # 결과 저장
        output_file = Path(__file__).parent / "step2_validation_report.json"
        with open(output_file, "w", encoding="utf-8") as f:
            rfp = state.get("rfp_analysis")
            report = {
                "timestamp": datetime.now().isoformat(),
                "project_id": state.get("project_id"),
                "rfp_title": rfp.project_name if rfp else "(없음)",
                "positioning": state.get("positioning"),
                "validation_findings": {
                    k: v for k, v in findings.items()
                    if k not in ["performance_metrics"] or isinstance(v, dict)
                },
                "performance_metrics": findings["performance_metrics"],
                "passed": findings["validation_score"] >= 70,
            }
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"결과 보고서: {output_file}")
        print()
        print("[OK] STEP 2 검증 완료")

    except Exception as e:
        print(f"[FAIL] STEP 2 실행 오류: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
