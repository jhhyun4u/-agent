"""
Phase 노드용 Mock 데이터 (v3.1.1 테스트용)

실제 LLM 호출 대신 하드코딩된 결과를 반환하여 그래프 구조 검증.
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add project root to path
_project_root = str(Path(__file__).parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from state.phase_artifacts import (
    PhaseArtifact_1_Research,
    PhaseArtifact_2_Analysis,
    PhaseArtifact_3_Plan,
    PhaseArtifact_4_Implement,
)


# ═══ Phase 1: Research Mock 데이터 ═══

MOCK_PHASE1_RESULT = {
    "parsed_rfp": {
        "title": "[모의] 클라우드 기반 디지털 전환 솔루션 구축",
        "client": "국가정보사회진흥원(NIA)",
        "deadline": "2026-03-31",
        "page_limit": 50,
        "budget_range": "5억~10억",
        "evaluation_method": "종합평가",
        "requirements": [
            {"id": "REQ-001", "category": "기술", "description": "AWS/Azure 클라우드 구축", "mandatory": True},
            {"id": "REQ-002", "category": "기술", "description": "마이크로서비스 아키텍처", "mandatory": True},
            {"id": "REQ-003", "category": "인력", "description": "클라우드 아키텍트 3명 이상", "mandatory": True},
            {"id": "REQ-004", "category": "보안", "description": "ISO 27001 인증", "mandatory": False},
            {"id": "REQ-005", "category": "일정", "description": "12개월 이내 완료", "mandatory": True},
        ],
        "evaluation_criteria": [
            {"category": "기술방안", "score": 40, "subcriteria": ["아키텍처 타당성", "기술 혁신성"]},
            {"category": "실행방안", "score": 30, "subcriteria": ["일정 관리", "리스크 관리"]},
            {"category": "가격", "score": 20, "subcriteria": ["적정성"]},
            {"category": "인력", "score": 10, "subcriteria": ["경험", "배치율"]},
        ],
    },
    "past_proposals": [
        {
            "id": "PAST-001",
            "title": "클라우드 마이그레이션 프로젝트",
            "client": "NIA",
            "score": 85,
            "result": "수주",
            "key_lesson": "마이크로서비스 설계가 평가 핵심",
        },
        {
            "id": "PAST-002",
            "title": "컨테이너 기반 인프라 구축",
            "client": "정보통신정책연구원",
            "score": 78,
            "result": "수주",
            "key_lesson": "DevOps 자동화 강조 필요",
        },
    ],
    "competition_history": [
        {"competitor": "삼존", "result": "우리 승리", "score_gap": 3},
        {"competitor": "LG CNS", "result": "패배", "score_gap": -5},
    ],
    "available_personnel": 12,
    "rfp_document_ref": "document_store://rfp-2026-001",
}


def create_mock_artifact_1() -> dict:
    """Phase 1 결과를 Artifact #1로 변환"""
    return {
        "rfp_title": MOCK_PHASE1_RESULT["parsed_rfp"]["title"],
        "client_name": MOCK_PHASE1_RESULT["parsed_rfp"]["client"],
        "submission_deadline": MOCK_PHASE1_RESULT["parsed_rfp"]["deadline"],
        "budget_range": MOCK_PHASE1_RESULT["parsed_rfp"]["budget_range"],
        "page_limit": MOCK_PHASE1_RESULT["parsed_rfp"]["page_limit"],
        "evaluation_method": MOCK_PHASE1_RESULT["parsed_rfp"]["evaluation_method"],
        "requirements_summary": MOCK_PHASE1_RESULT["parsed_rfp"]["requirements"][:5],
        "evaluation_criteria_raw": MOCK_PHASE1_RESULT["parsed_rfp"]["evaluation_criteria"],
        "past_proposals_summary": MOCK_PHASE1_RESULT["past_proposals"][:5],
        "competition_history": MOCK_PHASE1_RESULT["competition_history"],
        "company_capabilities_relevant": [
            "클라우드 아키텍처",
            "AWS/Azure",
            "마이크로서비스",
            "DevOps",
            "컨테이너화",
        ],
        "available_personnel_count": MOCK_PHASE1_RESULT["available_personnel"],
        "rfp_document_ref": MOCK_PHASE1_RESULT["rfp_document_ref"],
        "full_data_refs": {},
    }


# ═══ Phase 2: Analysis Mock 데이터 ═══

MOCK_PHASE2_RESULT = {
    "rfp_analysis": {
        "evaluation_criteria": [
            {
                "category": "기술방안",
                "score": 40,
                "weight": 0.40,
                "interpretation": "클라우드 아키텍처의 타당성과 혁신성을 40점으로 평가",
            },
            {
                "category": "실행방안",
                "score": 30,
                "weight": 0.30,
                "interpretation": "프로젝트 일정과 리스크 관리를 30점으로 평가",
            },
            {
                "category": "가격",
                "score": 20,
                "weight": 0.20,
                "interpretation": "예산 적정성을 20점으로 평가",
            },
            {
                "category": "인력",
                "score": 10,
                "weight": 0.10,
                "interpretation": "투입 인력의 경험과 배치율을 10점으로 평가",
            },
        ],
        "mandatory_requirements": [
            {"id": "REQ-001", "description": "AWS/Azure 클라우드", "status": "충족", "gap": ""},
            {"id": "REQ-002", "description": "마이크로서비스", "status": "충족", "gap": ""},
            {"id": "REQ-003", "description": "클라우드 아키텍트 3명", "status": "충족", "gap": ""},
        ],
        "implicit_intent": "발주처는 단순 클라우드 이전이 아닌 현대적 아키텍처 기반 디지털 전환을 희망. 마이크로서비스와 자동화에 높은 관심.",
        "risk_factors": [
            "클라우드 보안 정책이 엄격할 가능성",
            "레거시 시스템 통합 복잡도",
            "인력 확보 경쟁",
        ],
    },
    "competitive_analysis": {
        "landscape": "삼존, LG CNS, SK C&C가 주요 경쟁사. 우리는 마이크로서비스 경험에서 우위.",
        "our_strengths": [
            "마이크로서비스 아키텍처 설계 경험",
            "DevOps 자동화 역량",
            "과거 NIA 수주 경험",
            "빠른 프로토타이핑 능력",
        ],
        "our_weaknesses": [
            "대규모 엔터프라이즈 프로젝트 경험 부족",
            "보안 인증 (ISO 27001) 미충족",
            "LG CNS 대비 인지도 낮음",
        ],
        "strategy_hint": "마이크로서비스와 자동화를 핵심 차별화. 작은 규모의 민첩성을 강점으로.",
    },
    "section_allocations": [
        {"section_id": "sec_01", "section_name": "사업 이해도", "pages": 8, "depth": "deep"},
        {"section_id": "sec_02", "section_name": "기술 전략", "pages": 12, "depth": "deep"},
        {"section_id": "sec_03", "section_name": "실행 방안", "pages": 10, "depth": "deep"},
        {"section_id": "sec_04", "section_name": "조직", "pages": 5, "depth": "medium"},
        {"section_id": "sec_05", "section_name": "일정", "pages": 5, "depth": "medium"},
        {"section_id": "sec_06", "section_name": "예산", "pages": 4, "depth": "medium"},
        {"section_id": "sec_07", "section_name": "기대 효과", "pages": 3, "depth": "light"},
        {"section_id": "sec_08", "section_name": "리스크", "pages": 2, "depth": "light"},
        {"section_id": "sec_09", "section_name": "참고사항", "pages": 1, "depth": "light"},
    ],
    "qualification_status": "충족",
    "qualification_gaps": [],
}


def create_mock_artifact_2() -> dict:
    """Phase 2 결과를 Artifact #2로 변환"""
    return {
        "evaluation_criteria": MOCK_PHASE2_RESULT["rfp_analysis"]["evaluation_criteria"],
        "mandatory_requirements": MOCK_PHASE2_RESULT["rfp_analysis"]["mandatory_requirements"],
        "implicit_intent": MOCK_PHASE2_RESULT["rfp_analysis"]["implicit_intent"],
        "risk_factors": MOCK_PHASE2_RESULT["rfp_analysis"]["risk_factors"],
        "client_vocabulary": {
            "preferred_terms": ["디지털 전환", "클라우드 선오", "현대화"],
            "tone": "기술적이면서도 비즈니스 중심",
            "formality_level": "공식적",
        },
        "client_priorities": ["기술 혁신", "일정 준수", "보안", "비용 효율성"],
        "competitive_landscape": MOCK_PHASE2_RESULT["competitive_analysis"]["landscape"],
        "our_strengths": MOCK_PHASE2_RESULT["competitive_analysis"]["our_strengths"],
        "our_weaknesses": MOCK_PHASE2_RESULT["competitive_analysis"]["our_weaknesses"],
        "attack_strategy_hint": MOCK_PHASE2_RESULT["competitive_analysis"]["strategy_hint"],
        "section_allocations": MOCK_PHASE2_RESULT["section_allocations"],
        "total_target_pages": sum(s["pages"] for s in MOCK_PHASE2_RESULT["section_allocations"]),
        "qualification_status": MOCK_PHASE2_RESULT["qualification_status"],
        "qualification_gaps": MOCK_PHASE2_RESULT["qualification_gaps"],
        "phase1_artifact_ref": "phase_artifact_1",
    }


# ═══ Phase 3: Plan Mock 데이터 ═══

MOCK_PHASE3_RESULT = {
    "strategy": {
        "core_message": "마이크로서비스 기반 현대적 클라우드 아키텍처로 민첩한 디지털 전환을 실현합니다.",
        "win_themes": [
            "마이크로서비스 기반 유연한 아키텍처",
            "자동화된 DevOps로 빠른 배포",
            "보안 중심의 설계",
            "비용 효율적인 클라우드 운영",
        ],
        "differentiators": [
            "마이크로서비스 설계 경험 (과거 5개 프로젝트)",
            "자동화 CI/CD 파이프라인",
            "NIA와의 협력 경험",
        ],
        "section_plans": [
            {
                "section_id": "sec_01",
                "section_name": "사업 이해도",
                "target_pages": 8,
                "depth": "deep",
                "key_messages": ["발주처의 의도 정확히 이해", "과거 유사 프로젝트 성공"],
                "writing_guidelines": "발주처의 비즈니스 목표에 우리 솔루션을 매칭",
                "depends_on": [],
                "visual_plan": ["조직도"],
            },
            {
                "section_id": "sec_02",
                "section_name": "기술 전략",
                "target_pages": 12,
                "depth": "deep",
                "key_messages": ["마이크로서비스 아키텍처", "클라우드 네이티브"],
                "writing_guidelines": "기술적 세부사항과 비즈니스 가치의 균형",
                "depends_on": ["sec_01"],
                "visual_plan": ["아키텍처 다이어그램", "기술 스택 비교"],
            },
        ],
        "language_guidelines": {
            "tone": "기술적이면서 친근함",
            "preferred_terms": ["디지털 전환", "클라우드 선도", "마이크로서비스"],
            "avoid_terms": ["레거시", "구식"],
        },
    },
    "personnel": [
        {"role": "PM", "name": "홍길동", "grade": "이사", "certifications": ["PMP", "AWS Solution Architect"]},
        {
            "role": "기술 리더",
            "name": "김철수",
            "grade": "부장",
            "certifications": ["AWS Certified Solutions Architect", "Kubernetes"],
        },
        {"role": "아키텍트", "name": "이영준", "grade": "부장", "certifications": ["AWS", "MSA"]},
        {"role": "DevOps", "name": "박민준", "grade": "차장", "certifications": ["AWS", "Docker", "Kubernetes"]},
        {"role": "개발", "name": "최진호", "grade": "과장", "certifications": ["AWS", "Java", "Python"]},
    ],
    "generation_phases": [
        ["sec_01"],
        ["sec_02", "sec_04"],
        ["sec_03", "sec_05"],
        ["sec_06", "sec_07"],
        ["sec_08", "sec_09"],
    ],
    "rag_references": {
        "domain_general": [
            {
                "content": "[참고] 클라우드 마이그레이션 모범 사례: 단계적 접근이 성공률 높음",
                "metadata": {"source": "past_proposal", "score": 0.92},
            }
        ],
        "methodology": [
            {
                "content": "[방법론] 마이크로서비스 아키텍처 설계 패턴: 도메인별 분리, API 게이트웨이",
                "metadata": {"source": "company_knowledge", "score": 0.88},
            }
        ],
    },
}


def create_mock_artifact_3() -> dict:
    """Phase 3 결과를 Artifact #3로 변환"""
    return {
        "core_message": MOCK_PHASE3_RESULT["strategy"]["core_message"],
        "win_themes": MOCK_PHASE3_RESULT["strategy"]["win_themes"],
        "differentiators": MOCK_PHASE3_RESULT["strategy"]["differentiators"],
        "section_plans": MOCK_PHASE3_RESULT["strategy"]["section_plans"],
        "personnel_assignments": MOCK_PHASE3_RESULT["personnel"],
        "language_guidelines": MOCK_PHASE3_RESULT["strategy"]["language_guidelines"],
        "generation_phases": MOCK_PHASE3_RESULT["generation_phases"],
        "rag_references": MOCK_PHASE3_RESULT["rag_references"],
        "phase2_artifact_ref": "phase_artifact_2",
    }


# ═══ Phase 4: Implement Mock 데이터 ═══

MOCK_PHASE4_RESULT = {
    "sections": {
        "sec_01": {
            "section_id": "sec_01",
            "section_name": "사업 이해도",
            "content": "발주처는 기존 레거시 시스템을 현대적 클라우드 아키텍처로 전환하고자 합니다...",
            "actual_pages": 7.8,
            "key_messages_summary": "발주처 이해, 과거 경험",
            "key_claims": ["유사 프로젝트 성공 경험"],
            "numbers_used": ["NIA와 협력 5회", "마이크로서비스 도입 3건"],
        },
        "sec_02": {
            "section_id": "sec_02",
            "section_name": "기술 전략",
            "content": "마이크로서비스 기반 클라우드 네이티브 아키텍처를 제시합니다...",
            "actual_pages": 11.5,
            "key_messages_summary": "MSA, 자동화, 보안",
            "key_claims": ["MSA로 배포 시간 50% 단축"],
            "numbers_used": ["CI/CD 자동화율 95%", "비용 절감 30%"],
        },
        "sec_03": {
            "section_id": "sec_03",
            "section_name": "실행 방안",
            "content": "Phase별 추진으로 리스크를 최소화하고 빠른 가치 실현을 추구합니다...",
            "actual_pages": 9.2,
            "key_messages_summary": "Phase 기반, 리스크 관리",
            "key_claims": ["3개월 단위 Phase 진행"],
            "numbers_used": ["4 Phase, 12개월"],
        },
    },
    "section_refs": {
        "sec_01": "doc-001",
        "sec_02": "doc-002",
        "sec_03": "doc-003",
    },
}


def create_mock_artifact_4() -> dict:
    """Phase 4 결과를 Artifact #4로 변환"""
    total_pages = sum(s["actual_pages"] for s in MOCK_PHASE4_RESULT["sections"].values())
    return {
        "section_summaries": [
            {
                "section_id": s["section_id"],
                "section_name": s["section_name"],
                "summary": s["key_messages_summary"],
                "actual_pages": s["actual_pages"],
                "key_claims": s["key_claims"],
                "numbers_used": s["numbers_used"],
            }
            for s in MOCK_PHASE4_RESULT["sections"].values()
        ],
        "total_pages": total_pages,
        "total_target_pages": 50,
        "overall_traceability": 0.87,
        "section_full_refs": {
            k: f"document_store://{v}" for k, v in MOCK_PHASE4_RESULT["section_refs"].items()
        },
        "phase3_artifact_ref": "phase_artifact_3",
        "generation_notes": ["모든 섹션 1회차 생성 완료"],
    }


# ═══ Phase 5: Test & Finalize Mock 데이터 ═══

MOCK_PHASE5_RESULT = {
    "quality_score": 0.82,
    "critique_result": {
        "overall_score": 0.82,
        "individual_issues": [
            {"section": "sec_01", "severity": "low", "issue": "프롬프트 문체 약간 어색"},
            {"section": "sec_02", "severity": "medium", "issue": "기술 설명이 너무 상세"},
        ],
        "consistency_issues": [],
    },
    "revision_rounds": 0,
    "final_sections": MOCK_PHASE4_RESULT["sections"],
    "export_path": "/output/proposal-2026-001.docx",
}


def create_mock_phase5_working_state() -> dict:
    """Phase 5 작업 상태 초기화"""
    return {
        "sections": MOCK_PHASE5_RESULT["final_sections"],
        "quality_score": MOCK_PHASE5_RESULT["quality_score"],
        "critique_result": MOCK_PHASE5_RESULT["critique_result"],
        "revision_rounds": MOCK_PHASE5_RESULT["revision_rounds"],
        "export_path": "/output/proposal-2026-001.docx",
        "structural_issues": [],
    }


if __name__ == "__main__":
    # 테스트: Mock 데이터 검증
    artifact1 = create_mock_artifact_1()
    artifact2 = create_mock_artifact_2()
    artifact3 = create_mock_artifact_3()
    artifact4 = create_mock_artifact_4()

    print("✅ Mock 데이터 검증")
    print(f"  - Artifact #1: {len(str(artifact1))} bytes")
    print(f"  - Artifact #2: {len(str(artifact2))} bytes")
    print(f"  - Artifact #3: {len(str(artifact3))} bytes")
    print(f"  - Artifact #4: {len(str(artifact4))} bytes")
    print("\n✅ 모든 Mock 데이터 정상 생성")
