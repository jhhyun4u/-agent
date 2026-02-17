"""RFP 분석 에이전트 테스트"""
import asyncio
from agents.rfp_analysis_agent import build_rfp_analysis_graph


async def test_rfp_analysis():
    print("=" * 60)
    print("RFP 분석 에이전트 테스트")
    print("=" * 60)

    # Mock RFP 문서
    mock_rfp = """
    제안요청서

    사업명: 클라우드 기반 통합 플랫폼 구축 사업
    발주기관: 한국공공기관

    1. 사업 개요
    본 사업은 기존 레거시 시스템을 클라우드 환경으로 전환하고,
    통합 플랫폼을 구축하여 업무 효율성을 향상시키는 것을 목표로 합니다.

    2. 사업 범위
    - 클라우드 인프라 구축 (AWS 또는 Azure)
    - 마이크로서비스 아키텍처 설계 및 구현
    - 데이터 마이그레이션
    - 보안 체계 구축

    3. 평가 기준
    - 기술 능력: 40점
    - 수행 계획: 30점
    - 가격: 20점
    - 인력 구성: 10점

    4. 자격 요건
    필수 요건:
    - 클라우드 구축 경험 3건 이상
    - 정보처리기사 자격증 소지자 2명 이상

    우대 사항:
    - AWS 또는 Azure 인증 보유자
    - 공공기관 수행 경험

    5. 예산
    총 사업비: 5억원

    6. 제출 기한
    2024년 12월 31일까지
    """

    # 그래프 생성
    print("\n1. 그래프 생성...")
    graph = build_rfp_analysis_graph()
    print("   ✓ 그래프 생성 완료")

    # 초기 상태
    initial_state = {
        "raw_document": mock_rfp,
        "cleaned_text": "",
        "structural_result": {},
        "implicit_analysis": {},
        "language_profile": {},
        "qualifications": {},
        "rfp_analysis_result": {},
    }

    print("\n2. RFP 분석 실행...")
    print("   - 텍스트 추출 및 정제")
    print("   - 구조 분석 (LLM)")
    print("   - 숨은 의도 분석 (LLM)")
    print("   - 언어 프로필 생성 (LLM)")
    print("   - 자격 요건 검증 (LLM)")

    try:
        # 그래프 실행
        result = await graph.ainvoke(initial_state)

        print("\n3. 분석 결과:")
        print("=" * 60)

        analysis = result.get("rfp_analysis_result", {})

        print(f"\n[기본 정보]")
        print(f"  사업명: {analysis.get('rfp_title', 'N/A')}")
        print(f"  발주처: {analysis.get('client_name', 'N/A')}")
        print(f"  예산: {analysis.get('budget', 'N/A')}")
        print(f"  마감일: {analysis.get('deadline', 'N/A')}")

        print(f"\n[평가 기준]")
        for criterion in analysis.get('evaluation_criteria', [])[:3]:
            print(f"  - {criterion.get('criterion', 'N/A')}: {criterion.get('weight', 0)}점")

        print(f"\n[숨은 의도]")
        print(f"  {analysis.get('hidden_intent', 'N/A')[:100]}...")

        print(f"\n[자격 요건]")
        quals = analysis.get('qualifications', {})
        print(f"  필수: {len(quals.get('mandatory', []))}개")
        print(f"  선택: {len(quals.get('optional', []))}개")

        print(f"\n[완성도 점수]")
        print(f"  {analysis.get('completeness_score', 0):.2%}")

        print("\n" + "=" * 60)
        print("[SUCCESS] RFP 분석 완료!")
        print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] 분석 실패: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Note: .env에 ANTHROPIC_API_KEY가 필요합니다
    print("\n⚠️  이 테스트는 실제 Claude API를 호출합니다.")
    print("⚠️  .env 파일에 유효한 ANTHROPIC_API_KEY가 필요합니다.\n")

    asyncio.run(test_rfp_analysis())
