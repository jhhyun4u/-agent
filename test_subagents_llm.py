#!/usr/bin/env python
"""Sub-agent LLM 통합 테스트"""

import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

async def test_subagents():
    """Sub-agent 통합 테스트"""
    
    print("=" * 70)
    print("Sub-agent LLM Integration Test")
    print("=" * 70)
    
    # 1. Sub-agent 로드 확인
    try:
        from services.subagents import (
            Phase1ResearchAgent,
            Phase2AnalysisAgent,
            Phase3StrategyAgent,
            Phase4ImplementAgent,
            Phase5QualityAgent,
        )
        print("\n[1] Sub-agent 로드")
        print("    Phase1ResearchAgent: OK")
        print("    Phase2AnalysisAgent: OK")
        print("    Phase3StrategyAgent: OK")
        print("    Phase4ImplementAgent: OK")
        print("    Phase5QualityAgent: OK")
        print("    [OK] 모든 Sub-agent 로드 성공")
    except ImportError as e:
        print(f"\n[1] Import Error: {e}")
        print("    Sub-agent가 없으면 Mock 데이터 사용")
        return
    
    # 2. API 키 확인
    import os
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    print("\n[2] ANTHROPIC_API_KEY")
    if api_key:
        print(f"    설정됨: {api_key[:20]}...")
    else:
        print("    미설정! .env 파일에 ANTHROPIC_API_KEY 추가 필요")
        print("    예: ANTHROPIC_API_KEY=sk-ant-...")
        return
    
    # 3. Phase 1 테스트 (RFP 파싱)
    print("\n[3] Phase 1 (RFP Analysis) 테스트")
    try:
        agent_1 = Phase1ResearchAgent()
        
        rfp_sample = """
        【클라우드 마이그레이션 프로젝트】
        발주처: 삼성전자
        프로젝트명: 온프레미스 인프라 모던화
        마감일: 2024-12-31
        분량: 100페이지
        
        필수요건:
        - AWS/Azure 경험 5년 이상
        - SLA 99.99% 보장
        - 한글 지원 문서
        
        예산: 5억원 ~ 10억원
        """
        
        result_1 = await agent_1.invoke({
            "rfp_content": rfp_sample,
        })
        
        print(f"    Title: {result_1.rfp_title}")
        print(f"    Client: {result_1.client_name}")
        print(f"    Pages: {result_1.page_limit}")
        print("    [OK] Phase 1 테스트 성공")
    except Exception as e:
        print(f"    [ERROR] {e}")
        return
    
    # 4. Phase 2 테스트 (분석)
    print("\n[4] Phase 2 (Analysis) 테스트")
    try:
        agent_2 = Phase2AnalysisAgent()
        
        result_2 = await agent_2.invoke({
            "phase_artifact_1": {
                "rfp_title": result_1.rfp_title,
                "client_name": result_1.client_name,
                "mandatory_requirements": result_1.mandatory_requirements,
            },
            "company_profile": {
                "name": "TechCorp",
                "industry": "Cloud Services",
                "capabilities": "AWS/Azure 전문가 50명, DevOps 경험 10년",
            },
        })
        
        print(f"    Qualification: {result_2.qualification_status}")
        print(f"    Strengths: {len(result_2.our_strengths)}개")
        print(f"    Weaknesses: {len(result_2.our_weaknesses)}개")
        print("    [OK] Phase 2 테스트 성공")
    except Exception as e:
        print(f"    [ERROR] {e}")
        return
    
    print("\n" + "=" * 70)
    print("Sub-agent LLM 통합 준비 완료!")
    print("=" * 70)
    print("\n다음 단계:")
    print("1. Phase nodes의 Mock 데이터 → Sub-agent 호출 변경 완료")
    print("2. claude-3-5-sonnet-20241022 모델 사용")
    print("3. 각 Phase마다 구조화된 Pydantic 검증")
    print("\n실행: graph/phase_nodes.py의 USE_LLM 변수를 체크합니다")

if __name__ == "__main__":
    asyncio.run(test_subagents())
