"""통합 Supervisor 시스템 테스트"""
import asyncio
from graph.integrated_supervisor import (
    build_integrated_supervisor,
    get_supervisor_status,
    create_initial_state,
)


async def test_integrated_supervisor():
    """통합 Supervisor 시스템 전체 테스트"""

    print("=" * 70)
    print("통합 Supervisor 시스템 테스트")
    print("=" * 70)

    # ========================================
    # 1. 시스템 빌드
    # ========================================
    print("\n[1단계] 시스템 빌드")
    print("=" * 70)

    try:
        supervisor_graph = build_integrated_supervisor()
    except Exception as e:
        print(f"[ERROR] 시스템 빌드 실패: {e}")
        import traceback
        traceback.print_exc()
        return

    # ========================================
    # 2. 상태 확인
    # ========================================
    print("\n[2단계] 시스템 상태 확인")
    print("=" * 70)

    status = get_supervisor_status(supervisor_graph)
    print(f"상태: {status['status']}")
    print(f"노드: {status['nodes']}개")
    print(f"Sub-agent: {status['subagents']}개")
    print(f"HITL Gate: {status['hitl_gates']}개")
    print(f"체크포인터: {status['checkpointer']}")

    # ========================================
    # 3. Mock 데이터 준비
    # ========================================
    print("\n[3단계] Mock 데이터 준비")
    print("=" * 70)

    mock_rfp = """
    제안요청서

    사업명: 차세대 디지털 플랫폼 구축 사업
    발주기관: 한국전자통신연구원

    1. 사업 개요
    AI 기반 지능형 플랫폼을 구축하여 디지털 전환을 가속화합니다.

    2. 사업 범위
    - 플랫폼 아키텍처 설계
    - AI 모델 개발 및 통합
    - 사용자 인터페이스 구축
    - 보안 체계 수립

    3. 평가 기준
    - 기술 능력: 50점
    - 사업 수행 계획: 30점
    - 가격 경쟁력: 20점

    4. 예산: 15억원
    5. 기간: 18개월
    6. 제출 마감: 2024년 12월 31일
    """

    company_profile = {
        "name": "테크 이노베이션",
        "strengths": ["AI/ML", "클라우드", "플랫폼 개발"],
        "experience_years": 15,
        "notable_projects": ["공공기관 AI 플랫폼", "금융 빅데이터 시스템"],
    }

    print("[OK] RFP 문서 준비 완료")
    print(f"  - 사업명: 차세대 디지털 플랫폼 구축")
    print(f"  - 발주기관: 한국전자통신연구원")
    print(f"  - 예산: 15억원")

    print("[OK] 회사 프로필 준비 완료")
    print(f"  - 회사명: {company_profile['name']}")
    print(f"  - 강점: {', '.join(company_profile['strengths'])}")
    print(f"  - 경력: {company_profile['experience_years']}년")

    # ========================================
    # 4. 초기 상태 생성
    # ========================================
    print("\n[4단계] 초기 상태 생성")
    print("=" * 70)

    try:
        initial_state = create_initial_state(
            rfp_document=mock_rfp,
            company_profile=company_profile
        )
        print("[OK] 초기 상태 생성 완료")
        print(f"  - Current Phase: {initial_state.get('current_phase', 'N/A')}")
        print(f"  - Workflow Plan: {len(initial_state.get('workflow_plan', []))}개 단계")
    except Exception as e:
        print(f"[ERROR] 초기 상태 생성 실패: {e}")
        import traceback
        traceback.print_exc()
        return

    # ========================================
    # 5. 시스템 준비 완료
    # ========================================
    print("\n" + "=" * 70)
    print("[SUCCESS] 통합 Supervisor 시스템 준비 완료!")
    print("=" * 70)

    print("\n[시스템 구성]")
    print("  1. Supervisor 오케스트레이터 - 워크플로우 관리")
    print("  2. RFP 분석 에이전트 - 문서 분석 및 파싱")
    print("  3. 전략 수립 에이전트 - 경쟁 분석 및 전략")
    print("  4. 섹션 생성 에이전트 - 제안서 콘텐츠 작성")
    print("  5. 품질 관리 에이전트 - 품질 검토 및 개선")
    print("  6. 문서 출력 에이전트 - DOCX/PPTX 생성")
    print("  7. HITL 게이트 - 인간 승인 프로세스")

    print("\n[다음 단계]")
    print("  - 실제 Claude API 키 설정")
    print("  - 전체 워크플로우 실행 테스트")
    print("  - HITL 승인 프로세스 테스트")

    print("\n[NOTE] 실제 실행을 위해서는 유효한 ANTHROPIC_API_KEY가 필요합니다.")

    # ========================================
    # 6. (선택) 간단한 실행 테스트
    # ========================================
    print("\n" + "=" * 70)
    print("[테스트] 간단한 실행 테스트 (API 키 필요)")
    print("=" * 70)

    test_execution = input("\n실제 실행 테스트를 진행하시겠습니까? (y/N): ").strip().lower()

    if test_execution == 'y':
        print("\n실행 시작...")
        try:
            # 체크포인트 설정
            config = {"configurable": {"thread_id": "test_run_001"}}

            # 비동기 실행
            result = await supervisor_graph.ainvoke(initial_state, config)

            print("\n[OK] 실행 완료!")
            print(f"  - 최종 Phase: {result.get('current_phase', 'N/A')}")
            print(f"  - 에이전트 상태: {result.get('agent_status', {})}")
            print(f"  - 메시지: {len(result.get('messages', []))}개")

        except Exception as e:
            print(f"\n[ERROR] 실행 실패: {e}")
            print("   API 키를 확인하거나 나중에 다시 시도하세요.")
    else:
        print("\n테스트를 건너뜁니다.")

    print("\n" + "=" * 70)
    print("테스트 완료!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_integrated_supervisor())
