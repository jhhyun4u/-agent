"""
모듈러 아키텍처 테스트 스크립트
"""

import asyncio
import sys
import os

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modular_architecture_simple import ModularProposalWorkflow

async def test_modular_architecture():
    """모듈러 아키텍처 테스트"""

    print("=== 모듈러 제안서 생성 시스템 테스트 ===")

    # 워크플로우 초기화
    workflow = ModularProposalWorkflow()
    print("✓ 워크플로우 초기화 완료")

    # 테스트 데이터
    rfp_content = """사업명: AI 기반 데이터 분석 시스템 구축
발주처: 테크노베이션
예산: 100,000,000원
기간: 12개월
요구사항:
- Python 기반 AI 모델 개발
- 데이터 분석 및 시각화
- 클라우드 배포 (AWS/Azure)
- 보안 및 개인정보 보호 준수

평가기준:
- 기술성: 40%
- 가격: 30%
- 실적: 20%
- 제안서: 10%
"""

    company_profile = {
        'name': '테크노베이션',
        'technology_stack': ['Python', 'AI', 'Machine Learning', 'Cloud', 'AWS'],
        'expertise_areas': ['데이터 분석', 'AI 모델링', '시스템 통합'],
        'qualifications': ['ISO 9001', '정보통신공사업', 'AI 전문 기업 인증'],
        'certifications': ['ISO 27001', 'CSAP'],
        'cost_efficiency_score': 0.8,
        'innovation_capability': 0.85,
        'rnd_investment_ratio': 0.06,
        'financial_health_score': 0.75
    }

    market_analysis = {
        'potential_competitors': [
            {
                'name': '경쟁사 A',
                'strength_score': 0.7,
                'weakness_score': 0.3,
                'estimated_price': 95000000,
                'differentiators': ['가격 경쟁력']
            },
            {
                'name': '경쟁사 B',
                'strength_score': 0.8,
                'weakness_score': 0.2,
                'estimated_price': 105000000,
                'differentiators': ['기술 우위']
            }
        ]
    }

    past_proposals = [
        {
            'title': '빅데이터 분석 시스템 구축',
            'result': 'won',
            'budget': 80000000,
            'category': '데이터 분석',
            'technologies': ['Python', 'Hadoop', 'Spark']
        },
        {
            'title': 'AI 챗봇 시스템 개발',
            'result': 'won',
            'budget': 60000000,
            'category': 'AI 개발',
            'technologies': ['Python', 'TensorFlow', 'NLP']
        },
        {
            'title': '클라우드 마이그레이션',
            'result': 'lost',
            'budget': 120000000,
            'category': '클라우드',
            'technologies': ['AWS', 'Docker', 'Kubernetes']
        }
    ]

    try:
        # 워크플로우 실행
        print("\n=== 워크플로우 실행 시작 ===")
        result = await workflow.execute_workflow(
            session_id='test_session_001',
            rfp_content=rfp_content,
            company_profile=company_profile,
            market_analysis=market_analysis,
            past_proposals=past_proposals
        )

        print("\n=== 실행 결과 ===")
        print(f"세션 ID: {result['session_id']}")
        print(f"성공 여부: {result['success']}")
        print(f"총 실행 시간: {result['total_execution_time']:.2f}초")
        print(f"모듈 실행 수: {len(result['module_results'])}")

        if result['error_message']:
            print(f"오류 메시지: {result['error_message']}")

        # 모듈별 결과 출력
        print("\n=== 모듈별 실행 결과 ===")
        for i, module_result in enumerate(result['module_results'], 1):
            status = "✓" if module_result['success'] else "✗"
            print(f"{i}. {module_result['module_name']}: {status} ({module_result['execution_time']:.2f}초)")
            if module_result['error_message']:
                print(f"   오류: {module_result['error_message']}")

        # 최종 결과 분석
        if result['final_result']:
            print("\n=== 최종 결과 분석 ===")

            final_result = result['final_result']

            # RFP 검토 결과
            if hasattr(final_result, 'decision'):
                print(f"RFP 검토 결정: {final_result.decision.value}")
                print(".2f")

            # 전략 수립 결과
            elif hasattr(final_result, 'primary_strategy'):
                print(f"주요 전략: {final_result.primary_strategy.value if final_result.primary_strategy else 'N/A'}")
                if hasattr(final_result, 'target_price_range'):
                    price_min, price_max = final_result.target_price_range
                    print(f"목표 가격 범위: {price_min:,}원 ~ {price_max:,}원")

            # 병렬 작업 결과
            elif hasattr(final_result, 'overall_progress'):
                print(".1%")
                if hasattr(final_result, 'bottlenecks') and final_result.bottlenecks:
                    print(f"병목 현상: {len(final_result.bottlenecks)}건")

            # 최종 검토 결과
            elif hasattr(final_result, 'submission_ready'):
                print(".2f")
                print(f"승인 상태: {final_result.approval_status.value if hasattr(final_result, 'approval_status') else 'N/A'}")
                print(f"제출 준비 완료: {final_result.submission_ready}")

                if hasattr(final_result, 'ppt_path') and final_result.ppt_path:
                    print(f"PPT 파일: {final_result.ppt_path}")
                if hasattr(final_result, 'proposal_doc_path') and final_result.proposal_doc_path:
                    print(f"제안서 파일: {final_result.proposal_doc_path}")

        print("\n=== 테스트 완료 ===")

    except Exception as e:
        print(f"\n❌ 테스트 실행 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_modular_architecture())