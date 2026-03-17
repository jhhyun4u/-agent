"""
기술성 평가 최적화 분석 테스트
"""

import asyncio
from rfp_review_engine import RFPReviewEngine

async def test_technical_optimization():
    engine = RFPReviewEngine()
    
    rfp = {
        'basic_info': {
            'title': '디지털 환경영향평가 연구사업',
            'budget': 500000000,
            'category': '환경평가'
        },
        'requirements': {
            'technical_requirements': ['환경평가', '디지털화', '연구개발', 'AI', '데이터분석']
        },
        'evaluation_criteria': {
            'weights': {'기술성': 0.4, '가격': 0.3, '실적': 0.3}
        }
    }
    
    company = {
        'technology_stack': ['Python', 'AI', 'GIS', '디지털화'],
        'expertise_areas': ['환경평가', '데이터분석', '연구개발'],
        'innovation_capability': 0.75,
        'past_performance_score': 0.85,
        'team_capacity': 0.8,
        'past_proposals': [
            {'category': '환경평가', 'result': 'won'},
            {'category': '환경평가', 'result': 'won'}
        ]
    }
    
    try:
        result = await engine.analyze_technical_scoring_optimization(rfp, company, [])
        
        print('=' * 50)
        print('기술성 평가 점수 최적화 분석')
        print('=' * 50)
        print(f'현재 기술성 점수: {result.current_score:.1f}점')
        print(f'최대 가능 점수: {result.max_possible_score:.1f}점')
        print(f'달성률: {(result.current_score / result.max_possible_score * 100):.1f}%')
        print(f'예상 승률: {result.win_probability:.0%}')
        print()
        
        print('=' * 50)
        print('우선순위별 개선 방안')
        print('=' * 50)
        for i, improvement in enumerate(result.priority_improvements, 1):
            print(f'\n{i}. {improvement["항목"]}')
            print(f'   현재: {improvement["현재_점수"]:.0f}점 / 목표: {improvement["목표_점수"]:.0f}점')
            print(f'   우선순위: {improvement["우선순위"]}')
            print(f'   예상 점수 향상: {improvement["예상_점수_향상"]:.1%}')
            print(f'   개선 방법:')
            for method in improvement["개선_방법"][:3]:
                print(f'     - {method}')
        
        print()
        print('=' * 50)
        print('필요 증거 자료 (상위 10개)')
        print('=' * 50)
        for idx, evidence in enumerate(result.evidence_requirements[:10], 1):
            print(f'{idx}. {evidence}')
        
        print()
        print('=' * 50)
        print('점수 달성 시나리오')
        print('=' * 50)
        scenarios = [
            {'달성률': '95% 이상 (최고점수 기준)', '예상_승률': '85%', '필수_요소': '모든 세부항목 90점 이상'},
            {'달성률': '85-95% (상위 경쟁사)', '예상_승률': '65%', '필수_요소': '주요 항목 80점 이상'},
            {'달성률': '75-85% (경쟁 가능)', '예상_승률': '45%', '필수_요소': '최소 기본 요건 충족'},
        ]
        for scenario in scenarios:
            print(f"• {scenario['달성률']}")
            print(f"  → 예상 승률: {scenario['예상_승률']}")
            print(f"  → 필수 요소: {scenario['필수_요소']}")
        
    except Exception as e:
        print('오류 발생:', e)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_technical_optimization())
