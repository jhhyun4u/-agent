"""전체 Sub-agent 통합 테스트"""
import asyncio
from agents import (
    build_rfp_analysis_graph,
    build_strategy_graph,
    build_section_generation_graph,
    build_quality_graph,
    build_document_graph,
)


async def test_full_pipeline():
    """전체 에이전트 파이프라인 테스트"""

    print("=" * 70)
    print("전체 Sub-agent 파이프라인 테스트")
    print("=" * 70)

    # Mock RFP 문서
    mock_rfp = """
    제안요청서

    사업명: AI 기반 스마트 시티 플랫폼 구축
    발주기관: 서울시

    1. 사업 개요
    서울시 전역에 IoT 센서와 AI 분석 시스템을 구축하여
    도시 인프라를 지능화하고 시민 편의를 향상시키는 사업입니다.

    2. 사업 범위
    - IoT 센서 네트워크 구축
    - 실시간 데이터 수집 및 분석
    - AI 기반 예측 및 최적화
    - 시민 서비스 통합 플랫폼

    3. 평가 기준
    - 기술 능력: 40점
    - 사업 이해도: 25점
    - 수행 방법론: 20점
    - 가격: 15점

    4. 예산: 10억원
    5. 기간: 12개월
    """

    # ========================================
    # 1. RFP 분석 에이전트
    # ========================================
    print("\n" + "=" * 70)
    print("1️⃣  RFP 분석 에이전트")
    print("=" * 70)

    rfp_graph = build_rfp_analysis_graph()

    rfp_state = {
        "raw_document": mock_rfp,
        "cleaned_text": "",
        "structural_result": {},
        "implicit_analysis": {},
        "language_profile": {},
        "qualifications": {},
        "rfp_analysis_result": {},
    }

    try:
        rfp_result = await rfp_graph.ainvoke(rfp_state)
        rfp_analysis = rfp_result.get("rfp_analysis_result", {})

        print(f"✓ RFP 분석 완료")
        print(f"  - 사업명: {rfp_analysis.get('rfp_title', 'N/A')}")
        print(f"  - 발주처: {rfp_analysis.get('client_name', 'N/A')}")
        print(f"  - 평가 기준: {len(rfp_analysis.get('evaluation_criteria', []))}개")
        print(f"  - 완성도: {rfp_analysis.get('completeness_score', 0):.2%}")
    except Exception as e:
        print(f"✗ RFP 분석 실패: {e}")
        return

    # ========================================
    # 2. 전략 수립 에이전트
    # ========================================
    print("\n" + "=" * 70)
    print("2️⃣  전략 수립 에이전트")
    print("=" * 70)

    strategy_graph = build_strategy_graph()

    strategy_state = {
        "rfp_analysis": rfp_analysis,
        "company_profile": {"name": "우리 회사", "strengths": ["AI", "IoT"]},
        "competitive_analysis": {},
        "score_allocations": [],
        "strategy_draft": {},
        "personnel_assignments": [],
        "strategy_result": {},
    }

    try:
        strategy_result = await strategy_graph.ainvoke(strategy_state)
        strategy = strategy_result.get("strategy_result", {})

        print(f"✓ 전략 수립 완료")
        print(f"  - 핵심 메시지: {strategy.get('strategy', {}).get('core_message', 'N/A')[:50]}...")
        print(f"  - 차별화 포인트: {len(strategy.get('strategy', {}).get('differentiators', []))}개")
        print(f"  - 섹션 배분: {len(strategy.get('score_allocations', []))}개")
        print(f"  - 인력 구성: {len(strategy.get('personnel', []))}명")
    except Exception as e:
        print(f"✗ 전략 수립 실패: {e}")
        import traceback
        traceback.print_exc()
        return

    # ========================================
    # 3. 섹션 생성 에이전트
    # ========================================
    print("\n" + "=" * 70)
    print("3️⃣  섹션 생성 에이전트")
    print("=" * 70)

    section_graph = build_section_generation_graph()

    section_state = {
        "rfp_analysis": rfp_analysis,
        "strategy": strategy.get("strategy", {}),
        "allocations": strategy.get("score_allocations", []),
        "generation_phases": [],
        "current_phase_index": 0,
        "remaining_phases": [],
        "generated_sections": {},
        "section_dependencies": {},
        "sections_result": {},
    }

    try:
        section_result = await section_graph.ainvoke(section_state)
        sections = section_result.get("sections_result", {})

        print(f"✓ 섹션 생성 완료")
        print(f"  - 총 섹션: {sections.get('total_sections', 0)}개")
        print(f"  - 상태: {sections.get('status', 'N/A')}")

        for section_name in list(sections.get('sections', {}).keys())[:3]:
            section_data = sections['sections'][section_name]
            print(f"  - {section_name}: {section_data.get('word_count', 0)}자")
    except Exception as e:
        print(f"✗ 섹션 생성 실패: {e}")
        import traceback
        traceback.print_exc()
        return

    # ========================================
    # 4. 품질 관리 에이전트
    # ========================================
    print("\n" + "=" * 70)
    print("4️⃣  품질 관리 에이전트")
    print("=" * 70)

    quality_graph = build_quality_graph()

    quality_state = {
        "sections": sections.get("sections", {}),
        "rfp_analysis": rfp_analysis,
        "critique_result": {},
        "integration_issues": [],
        "quality_score": 0.0,
        "revision_round": 0,
        "quality_action": "pass",
        "escalation_reason": None,
        "quality_result": {},
    }

    try:
        quality_result = await quality_graph.ainvoke(quality_state)
        quality = quality_result.get("quality_result", {})

        print(f"✓ 품질 검토 완료")
        print(f"  - 품질 점수: {quality.get('quality_score', 0):.2%}")
        print(f"  - 액션: {quality.get('action', 'N/A')}")
        print(f"  - 이슈: {len(quality.get('issues', []))}개")
    except Exception as e:
        print(f"✗ 품질 검토 실패: {e}")
        import traceback
        traceback.print_exc()
        return

    # ========================================
    # 5. 문서 출력 에이전트
    # ========================================
    print("\n" + "=" * 70)
    print("5️⃣  문서 출력 에이전트")
    print("=" * 70)

    document_graph = build_document_graph()

    document_state = {
        "sections": sections.get("sections", {}),
        "metadata": {
            "project_name": rfp_analysis.get("rfp_title", "제안서"),
            "client_name": rfp_analysis.get("client_name", "고객사"),
        },
        "executive_summary": "",
        "final_edited": {},
        "docx_content": None,
        "pptx_content": None,
        "export_paths": {},
        "document_result": {},
    }

    try:
        document_result = await document_graph.ainvoke(document_state)
        document = document_result.get("document_result", {})

        print(f"✓ 문서 생성 완료")
        print(f"  - 요약문: {len(document.get('executive_summary', ''))}자")

        export_paths = document.get("export_paths", {})
        if export_paths.get("docx"):
            print(f"  - DOCX: {export_paths['docx']}")
        if export_paths.get("pptx"):
            print(f"  - PPTX: {export_paths['pptx']}")
    except Exception as e:
        print(f"✗ 문서 생성 실패: {e}")
        import traceback
        traceback.print_exc()
        return

    # ========================================
    # 완료
    # ========================================
    print("\n" + "=" * 70)
    print("🎉 전체 파이프라인 테스트 완료!")
    print("=" * 70)


if __name__ == "__main__":
    print("\n⚠️  이 테스트는 실제 Claude API를 호출합니다.")
    print("⚠️  .env 파일에 유효한 ANTHROPIC_API_KEY가 필요합니다.\n")

    asyncio.run(test_full_pipeline())
